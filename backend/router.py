"""
router.py - The Brain of A-01 ModelRouter
------------------------------------------
For every prompt:
  1. Understand it  - the neural PromptAnalyzer (brain/) infers task type, complexity tier,
                      answer length and uncertainty. No keyword lists or hand-written rules.
  2. Derive needs   - required capability (with an uncertainty safety margin), required
                      context window, vision.
  3. Merge with the judge's live constraints (Max Latency, Max Cost/Token, Min Capability,
     Min Context). The stricter value always wins; nothing is ever relaxed.
  4. Filter         - hard constraints (constraint_engine.check_model).
  5. Rank           - latency, capability, reliability, task suitability, cost, load, tier.
  6. Explain        - every number behind the decision is returned.
"""

import uuid
from typing import Dict, List, Optional

from brain import PromptProfile, get_analyzer
from constraint_engine import FACTORS, ConstraintEngine, resolve_weights
from models import ModelProfile
from telemetry import Telemetry, telemetry as default_telemetry

FACTOR_LABELS = {
    "latency": "speed", "capability": "capability", "reliability": "reliability",
    "task_suitability": "task suitability", "cost": "cost", "load": "current load",
}


def _num(v) -> Optional[float]:
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def build_hard_constraints(constraints: dict, profile: PromptProfile) -> dict:
    """Merge judge constraints with the prompt's own requirements (stricter wins)."""
    c = constraints or {}
    judge_lat = _num(c.get("max_latency_ms"))
    judge_cost = _num(c.get("max_cost_per_token"))
    if judge_cost is None and _num(c.get("max_cost_per_1k_tokens")) is not None:
        judge_cost = float(c["max_cost_per_1k_tokens"]) / 1000.0
    judge_cap = _num(c.get("min_capability", c.get("min_capability_score"))) or 0.0
    judge_ctx = _num(c.get("min_context_length", c.get("required_context_length"))) or 0.0

    cap = max(judge_cap, profile.required_capability)
    ctx = max(judge_ctx, float(profile.required_context_tokens))
    return {
        "max_latency_ms": judge_lat,
        "max_cost_per_token": judge_cost,
        "min_capability": round(cap, 2),
        "min_context_length": int(ctx),
        "needs_vision": profile.needs_vision,
        "_capability_source": " (judge minimum)" if judge_cap >= profile.required_capability else " (needed by prompt)",
        "_context_source": " (judge minimum)" if judge_ctx >= profile.required_context_tokens else " (needed by prompt)",
    }


class ModelRouter:
    def __init__(self, telemetry: Optional[Telemetry] = None):
        self._engine = ConstraintEngine()
        self._analyzer = get_analyzer()
        self._telemetry = telemetry or default_telemetry

    def analyze(self, prompt: str, has_images: bool = False) -> PromptProfile:
        return self._analyzer.analyze(prompt, has_images=has_images)

    def route(self, prompt: str, constraints: Optional[dict], models: Dict[str, ModelProfile],
              request_id: Optional[str] = None, has_images: bool = False,
              profile: Optional[PromptProfile] = None) -> dict:
        request_id = request_id or str(uuid.uuid4())[:8]
        constraints = constraints or {}
        profile = profile or self.analyze(prompt, has_images)

        # Check for direct user model selection
        explicit_model_raw = constraints.get("preferred_model") or constraints.get("model")
        if explicit_model_raw and isinstance(explicit_model_raw, str) and explicit_model_raw.strip().lower() != "auto":
            target_key = explicit_model_raw.strip()
            if target_key not in models:
                val_lower = target_key.lower()
                for k, mod in models.items():
                    if k.lower() == val_lower or mod.name.lower() == val_lower or val_lower in mod.name.lower():
                        target_key = k
                        break
            if target_key in models:
                m = models[target_key]
                candidates = []
                for key, mod in models.items():
                    is_sel = (key == target_key)
                    candidates.append({
                        "model_id": key, "model_key": key, "name": mod.name, "role": mod.role,
                        "status": "selected" if is_sel else "passed",
                        "rejection_reason": None,
                        "violations": [],
                        "avg_latency_ms": mod.avg_latency_ms, "max_latency_ms": mod.max_latency_ms,
                        "worst_case_latency_ms": mod.max_latency_ms,
                        "capability_score": mod.capability_score, "context_length": mod.context_length,
                        "cost_per_1k_tokens": mod.cost_per_1k_tokens, "available": mod.available, "tier": mod.tier,
                        "score": 100.0 if is_sel else 0.0,
                        "rank": 1 if is_sel else 2,
                    })
                candidates.sort(key=lambda c: (0 if c["model_key"] == target_key else 1, c["name"]))
                return {
                    "request_id": request_id,
                    "status": "SUCCESS",
                    "selected": target_key,
                    "selected_name": m.name,
                    "candidates": candidates,
                    "ranking": [target_key],
                    "explanation": f"User explicitly selected {m.name}. Direct response without router intervention.",
                    "complexity": profile.to_dict(),
                    "analysis": profile.to_dict(),
                    "judge_constraints": constraints,
                    "effective_constraints": {},
                    "preference_used": "direct_user_selection",
                    "weights": {},
                    "failover_chain": [target_key],
                }

        hard = build_hard_constraints(constraints, profile)
        mode, weights = resolve_weights(constraints.get("preference"), profile.tier_distribution)
        tel = self._telemetry

        passed: List[ModelProfile] = []
        candidates: List[dict] = []
        for key, m in models.items():
            check = self._engine.check_model(m, hard, inflight=tel.inflight(key))
            if check.passes:
                passed.append(m)
            candidates.append({
                "model_id": key, "model_key": key, "name": m.name, "role": m.role,
                "status": "passed" if check.passes else "rejected",
                "rejection_reason": None if check.passes else "; ".join(check.violations),
                "violations": check.violations,
                "avg_latency_ms": m.avg_latency_ms, "max_latency_ms": m.max_latency_ms,
                "worst_case_latency_ms": check.worst_case_latency_ms,
                "capability_score": m.capability_score, "context_length": m.context_length,
                "cost_per_1k_tokens": m.cost_per_1k_tokens, "available": m.available, "tier": m.tier,
                "score": None,
            })

        public_hard = {k: v for k, v in hard.items() if not k.startswith("_")}
        base = {
            "request_id": request_id,
            "complexity": profile.to_dict(),
            "analysis": profile.to_dict(),
            "judge_constraints": constraints,
            "effective_constraints": public_hard,
            "preference_used": mode,
            "weights": weights,
            "failover_chain": [],
        }

        if not passed:
            return {
                **base,
                "status": "NO_VALID_MODEL",
                "selected": None,
                "candidates": candidates,
                "message": "No available model satisfies all hard constraints.",
                "explanation": self._explain_rejection(candidates, public_hard),
            }

        ranked = self._engine.score_models(
            passed, weights, mode, profile.task_distribution, profile.expected_output_tokens, hard,
            reliability_of=tel.reliability, inflight_of=tel.inflight)
        winner = ranked[0]
        by_key = {r.model_key: (i + 1, r) for i, r in enumerate(ranked)}
        for c in candidates:
            if c["model_key"] in by_key:
                rank, r = by_key[c["model_key"]]
                c["score"], c["score_breakdown"], c["rank"] = r.score, r.score_breakdown, rank
                if r.model_key == winner.model_key:
                    c["status"] = "selected"
        candidates.sort(key=lambda c: (c.get("rank") or 99, c["name"]))

        return {
            **base,
            "status": "SUCCESS",
            "selected": winner.model_key,
            "selected_name": winner.profile.name,
            "candidates": candidates,
            "ranking": [r.model_key for r in ranked],
            "explanation": self._explain_win(profile, ranked, weights, len(models)),
        }

    @staticmethod
    def _explain_win(profile: PromptProfile, ranked, weights: Dict[str, float], n_models: int) -> str:
        w = ranked[0]
        bd = w.score_breakdown
        task = profile.task.replace("_", " ")
        msg = (f"{w.profile.name} selected (score {w.score:.1f}/100) for {'an' if profile.tier[0] in 'aeiou' else 'a'} {profile.tier} {task} request. "
               f"{len(ranked)} of {n_models} models met every hard constraint.")
        if len(ranked) > 1:
            r = ranked[1]
            gains = sorted(
                ((weights[f] * (bd[f + '_score'] - r.score_breakdown[f + '_score']), f) for f in FACTORS),
                reverse=True)
            top = [FACTOR_LABELS[f] for g, f in gains if g > 0.05][:2]
            if top:
                msg += f" It beat {r.profile.name} ({r.score:.1f}) mainly on {' and '.join(top)}."
            else:
                msg += f" Runner-up: {r.profile.name} ({r.score:.1f})."
        heaviest = sorted(weights, key=weights.get, reverse=True)[:2]
        msg += f" Highest-weighted factors for this prompt: {FACTOR_LABELS[heaviest[0]]} and {FACTOR_LABELS[heaviest[1]]}."
        return msg

    @staticmethod
    def _explain_rejection(candidates: List[dict], hard: dict) -> str:
        counts: Dict[str, int] = {}
        for c in candidates:
            for v in c.get("violations", []):
                kind = v.split(" ")[0] + " " + v.split(" ")[1] if " " in v else v
                counts[kind] = counts.get(kind, 0) + 1
        main = ", ".join(f"{k.lower()} ({n} models)" for k, n in sorted(counts.items(), key=lambda x: -x[1])[:3])
        return ("Every model violates at least one non-negotiable constraint, so the request was rejected rather than "
                f"sent to a model that would break it. Most common violations: {main}. "
                f"Effective limits: capability >= {hard['min_capability']}, context >= {hard['min_context_length']:,} tokens"
                + (f", latency <= {int(hard['max_latency_ms'])}ms" if hard.get("max_latency_ms") else "") + ".")
