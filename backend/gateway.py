"""
gateway.py - Flask API Gateway for A-01 ModelRouter
----------------------------------------------------
Coordinates:
- Pipeline A: Model Configuration (PATCH /api/models/{model_id}, Reset, Get)
- Pipeline B: Runtime Model Routing (POST /api/infer, POST /api/route, POST /api/analyze)
- Observability: GET /api/logs, GET /api/stats, GET /api/health, GET /api/brain
"""

import os
import time
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from brain import get_analyzer
from constraint_engine import ConstraintEngine
from logger import routing_logger
from model_adapter import ModelAdapter
from models import registry
from router import ModelRouter
from telemetry import telemetry

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.environ.get("CORS_ORIGINS", "*").split(",")}})

_router = ModelRouter()
_adapter = ModelAdapter()
_engine = ConstraintEngine()

MAX_FAILOVER = 3
# When true, an answer that arrives slower than the judge's Max Latency counts as a failure and
# triggers failover. Off by default because local CPU inference is slower than the configured profiles.
STRICT_LATENCY = os.environ.get("STRICT_LATENCY", "false").lower() in ("1", "true", "yes")
_brain_eval_cache: dict = {}


def _error(message: str, status: int = 400, extra: dict = None) -> tuple:
    payload = {"success": False, "error": message}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _ok(data: dict, status: int = 200) -> tuple:
    return jsonify({"success": True, **data}), status


def _parse_request():
    body = request.get_json(silent=True) or {}
    prompt = str(body.get("prompt", "")).strip()
    constraints = body.get("constraints") or {}
    images = body.get("images") or []
    if not prompt:
        return None, _error("'prompt' is required and must not be empty.")
    if not isinstance(images, list) or not all(isinstance(i, str) for i in images):
        return None, _error("'images' must be a list of base64 strings.")
    valid, errs = _engine.validate_constraints(constraints)
    if not valid:
        return None, _error(f"Invalid constraints: {'; '.join(errs)}")
    return (prompt, constraints, images), None


# ===========================================================================
# Pipeline A: Model Configuration API
# ===========================================================================

@app.route("/api/health", methods=["GET"])
def health():
    all_models = registry.get_all()
    return _ok({
        "status": "ok",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_count": len(all_models),
        "available_models": sum(1 for m in all_models.values() if m.available),
        "version": "3.0.0",
        "router": "neural",
    })


@app.route("/api/models", methods=["GET"])
def get_models():
    models = registry.to_list()
    for m in models:
        m["runtime"] = telemetry.snapshot(m["model_key"])
        m["reliability_observed"] = round(telemetry.reliability(m["model_key"], m["reliability"]), 4)
    return _ok({"models": models, "count": len(models)})


@app.route("/api/models/<model_id>", methods=["PATCH"])
def update_model(model_id: str):
    """Judge edits model parameters (latency, capability, context, reliability, availability, cost, tier, task_affinity ...)."""
    if not registry.exists(model_id):
        return _error(f"Model '{model_id}' not found.", 404)
    body = request.get_json(silent=True) or {}
    if not body:
        return _error("Request body must be a non-empty JSON object.")
    updated_profile, err = registry.update(model_id, body)
    if err:
        return _error(err, 400)

    routing_logger.log_request(
        request_id=f"cfg-{str(uuid.uuid4())[:6]}",
        prompt=f"[CONFIG_UPDATE] Model '{model_id}' updated",
        constraints=body,
        decision={"type": "CONFIG_UPDATE", "model_id": model_id, "changes": body},
        response_time_ms=0,
        success=True,
        model_used=model_id,
        simulated=False,
    )
    return _ok({
        "message": f"Configuration for model '{model_id}' updated and persisted.",
        "model": updated_profile.to_dict(),
    })


@app.route("/api/models/reset", methods=["POST"])
def reset_models():
    """Reset all models to defaults and clear observed runtime history."""
    restored = registry.reset()
    telemetry.reset()
    return _ok({"message": "All models restored to factory defaults.", "models": restored})


# ===========================================================================
# Pipeline B: Runtime Inference & Routing API
# ===========================================================================

@app.route("/api/analyze", methods=["POST"])
def analyze_prompt():
    """What the brain understands about a prompt (no routing, no execution)."""
    body = request.get_json(silent=True) or {}
    prompt = str(body.get("prompt", "")).strip()
    if not prompt:
        return _error("'prompt' is required and must not be empty.")
    profile = _router.analyze(prompt, has_images=bool(body.get("images")))
    return _ok({"analysis": profile.to_dict()})


@app.route("/api/route", methods=["POST"])
def dry_run_route():
    parsed, err = _parse_request()
    if err:
        return err
    prompt, constraints, images = parsed
    decision = _router.route(prompt, constraints, registry.get_all(), has_images=bool(images))
    return _ok({"decision": decision})


@app.route("/api/infer", methods=["POST"])
def infer():
    wall_start = time.time()
    parsed, err = _parse_request()
    if err:
        return err
    prompt, constraints, images = parsed

    request_id = str(uuid.uuid4())[:8]
    all_models = registry.get_all()
    profile = _router.analyze(prompt, has_images=bool(images))
    judge_latency = constraints.get("max_latency_ms")

    audit_trail, excluded, failover_chain = [], set(), []
    final_decision = final_response = final_model = last_error = None
    exec_mode = "EXECUTION_ERROR"

    # Routing + failover loop: every hop is re-routed under the SAME hard constraints.
    for attempt in range(1, MAX_FAILOVER + 2):
        candidates = {k: v for k, v in all_models.items() if k not in excluded}
        if not candidates:
            last_error = "All eligible models exhausted during failover."
            break

        decision = _router.route(prompt, constraints, candidates, request_id, has_images=bool(images), profile=profile)
        # Show models that already failed in this request as rejected, so the explanation is complete.
        for k in excluded:
            m = all_models[k]
            decision["candidates"].append({
                "model_id": k, "model_key": k, "name": m.name, "role": m.role, "status": "rejected",
                "rejection_reason": "Failed during this request (excluded by failover)",
                "violations": ["Failed during this request"], "avg_latency_ms": m.avg_latency_ms,
                "max_latency_ms": m.max_latency_ms, "capability_score": m.capability_score,
                "cost_per_1k_tokens": m.cost_per_1k_tokens, "available": m.available, "score": None,
            })
        selected = decision.get("selected")
        final_decision = decision
        if not selected:
            last_error = decision.get("message", "No available model satisfies all hard constraints.")
            break

        failover_chain.append(selected)
        decision["failover_chain"] = list(failover_chain)
        profile_m = all_models[selected]

        with telemetry.track(selected):
            result = _adapter.call_model(profile_m, prompt, profile.expected_output_tokens, images or None)

        breached = bool(result["success"] and judge_latency and result["latency_ms"] > judge_latency)
        success = result["success"] and not (breached and STRICT_LATENCY)
        telemetry.record(selected, success, result["latency_ms"])

        audit_trail.append({
            "attempt": attempt,
            "model_key": selected,
            "model_name": profile_m.name,
            "success": success,
            "latency_ms": result["latency_ms"],
            "sla_breached": breached,
            "simulated": False,
            "execution_mode": result.get("execution_mode"),
            "error": result.get("error") or (f"Answered in {result['latency_ms']}ms, over Max Latency {judge_latency}ms"
                                             if breached and STRICT_LATENCY else None),
        })
        exec_mode = result.get("execution_mode", exec_mode)

        if success:
            final_response, final_model = result["text"], selected
            break
        excluded.add(selected)
        last_error = audit_trail[-1]["error"]

    failover_count = max(0, len(audit_trail) - 1)
    total_ms = int((time.time() - wall_start) * 1000)
    routing_logger.log_request(
        request_id=request_id,
        prompt=prompt,
        constraints=constraints,
        decision=final_decision or {},
        response_time_ms=total_ms,
        success=final_model is not None,
        error=None if final_model else last_error,
        model_used=final_model,
        simulated=False,
        failover_count=failover_count,
    )

    if final_model is not None:
        return _ok({
            "response": final_response,
            "model_used": final_model,
            "model_name": all_models[final_model].name,
            "decision": final_decision,
            "audit_trail": audit_trail,
            "latency_ms": total_ms,
            "failover_count": failover_count,
            "simulated": False,
            "execution_mode": exec_mode,
            "sla_breached": audit_trail[-1]["sla_breached"],
        })
    # NO_VALID_MODEL is returned with HTTP 200 so the UI can render the full explanation.
    return jsonify({
        "success": False,
        "status": "NO_VALID_MODEL",
        "message": "No available model satisfies all hard constraints."
        if not audit_trail else "Every eligible model failed; no constraint was relaxed.",
        "error": last_error or "No available model satisfies all hard constraints.",
        "decision": final_decision,
        "audit_trail": audit_trail,
        "latency_ms": total_ms,
    }), 200


# ===========================================================================
# Observability
# ===========================================================================

@app.route("/api/logs", methods=["GET"])
def get_logs():
    try:
        limit = int(request.args.get("limit", 100))
    except Exception:
        limit = 100
    logs = routing_logger.get_logs(limit=limit)
    return _ok({"logs": logs, "count": len(logs)})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    return _ok({"stats": routing_logger.get_stats()})


@app.route("/api/brain", methods=["GET"])
def brain_info():
    """Routing brain metadata and its measured accuracy on the held-out evaluation set."""
    if not _brain_eval_cache:
        from brain.evaluate import evaluate_all
        _brain_eval_cache.update(evaluate_all())
    return _ok({"brain": get_analyzer().info, "evaluation": _brain_eval_cache})


if __name__ == "__main__":
    get_analyzer().ensure_ready()  # trains on first run, then loads from cache
    port = int(os.environ.get("PORT", 5000))
    print(f"[ModelRouter] Gateway running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
            use_reloader=False)
