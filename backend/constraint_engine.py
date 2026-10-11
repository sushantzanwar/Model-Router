"""
constraint_engine.py - Hard constraints + multi-factor scoring for A-01 ModelRouter
------------------------------------------------------------------------------------
Stage 1 - Hard constraints (non-negotiable; one violation = rejected):
   * availability / enabled
   * queue-adjusted worst-case latency  <= judge's Max Latency
   * cost per token                     <= judge's Max Cost / Token
   * capability score                   >= max(judge's Min Capability, capability the prompt needs)
   * context window                     >= max(judge's Min Context, tokens the prompt needs)
   * vision support                     if the request carries images

Stage 2 - Scoring of the survivors (0-100), seven factors:
   latency, capability, reliability, task suitability, cost, current load, tier
   Weights are chosen continuously from the prompt's complexity distribution (or from an
   explicit preference), so simple prompts favour speed and hard prompts favour capability.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from models import ModelProfile

FACTORS = ["latency", "capability", "reliability", "task_suitability", "cost", "load"]

# Weight profile per complexity tier; the router blends these by the tier probabilities.
TIER_WEIGHTS = {
    # simple prompts: any model above the capability floor is good enough -> extra capability is only wasted latency
    "simple":   {"latency": 0.45, "capability": 0.00, "reliability": 0.15, "task_suitability": 0.25, "cost": 0.05, "load": 0.10},
    "moderate": {"latency": 0.30, "capability": 0.12, "reliability": 0.15, "task_suitability": 0.28, "cost": 0.05, "load": 0.10},
    "complex":  {"latency": 0.14, "capability": 0.30, "reliability": 0.15, "task_suitability": 0.29, "cost": 0.04, "load": 0.08},
    "expert":   {"latency": 0.08, "capability": 0.38, "reliability": 0.14, "task_suitability": 0.30, "cost": 0.04, "load": 0.06},
}
PREFERENCE_WEIGHTS = {
    "lowest_latency":     {"latency": 0.60, "capability": 0.05, "reliability": 0.12, "task_suitability": 0.13, "cost": 0.03, "load": 0.07},
    "highest_capability": {"latency": 0.05, "capability": 0.55, "reliability": 0.12, "task_suitability": 0.22, "cost": 0.02, "load": 0.04},
    "cheapest":           {"latency": 0.12, "capability": 0.08, "reliability": 0.10, "task_suitability": 0.15, "cost": 0.50, "load": 0.05},
    "balanced":           {"latency": 0.22, "capability": 0.20, "reliability": 0.15, "task_suitability": 0.25, "cost": 0.08, "load": 0.10},
}
PREFERENCE_ALIASES = {"fastest": "lowest_latency", "quality": "highest_capability"}
EXPERIMENTAL_PENALTY = 0.05      # applied under balanced / auto routing
LATENCY_REF_MS = 10000.0         # normalisation when the judge sets no latency budget
COST_REF_PER_TOKEN = 0.001       # normalisation when the judge sets no cost ceiling
TYPICAL_ANSWER_TOKENS = 450      # answer length that a model's avg latency corresponds to


@dataclass
class CheckResult:
    passes: bool
    violations: List[str]
    worst_case_latency_ms: int


@dataclass
class RankedModel:
    model_key: str
    profile: ModelProfile
    score: float
    score_breakdown: Dict[str, float]


def resolve_weights(preference: Optional[str], tier_distribution: Dict[str, float]) -> Tuple[str, Dict[str, float]]:
    pref = (preference or "auto").lower()
    pref = PREFERENCE_ALIASES.get(pref, pref)
    if pref in PREFERENCE_WEIGHTS:
        return pref, dict(PREFERENCE_WEIGHTS[pref])
    blended = {f: 0.0 for f in FACTORS}
    for tier, p in tier_distribution.items():
        for f in FACTORS:
            blended[f] += p * TIER_WEIGHTS[tier][f]
    total = sum(blended.values()) or 1.0
    return "auto", {f: round(v / total, 4) for f, v in blended.items()}


class ConstraintEngine:

    # ------------------------------------------------------------------
    # Stage 1: hard constraints
    # ------------------------------------------------------------------
    def check_model(self, model: ModelProfile, hard: dict, inflight: int = 0) -> CheckResult:
        v: List[str] = []

        if not model.availability or not model.enabled:
            states = [s for s, bad in (("offline/unavailable", not model.availability), ("disabled", not model.enabled)) if bad]
            v.append(f"Model is {' and '.join(states)}")

        # Worst case = configured upper bound, plus one extra full slot of waiting if the model is saturated.
        queued = max(0, inflight - model.max_concurrency + 1)
        worst = int(model.max_latency_ms * (1 + queued))
        budget = hard.get("max_latency_ms")
        if budget:
            if worst > budget:
                extra = f" incl. queue of {queued}" if queued else ""
                v.append(f"Worst-case latency {worst}ms{extra} exceeds Max Latency {int(budget)}ms")

        max_cost = hard.get("max_cost_per_token")
        if max_cost is not None and model.cost_per_token > max_cost + 1e-15:
            v.append(f"Cost ${model.cost_per_token:.6f}/token exceeds Max Cost ${max_cost:.6f}/token")

        min_cap = hard.get("min_capability")
        if min_cap and model.capability_score + 1e-9 < min_cap:
            src = hard.get("_capability_source", "")
            v.append(f"Capability {model.capability_score:.1f} below required {min_cap:.1f}{src}")

        min_ctx = hard.get("min_context_length")
        if min_ctx and model.context_length < min_ctx:
            src = hard.get("_context_source", "")
            v.append(f"Context window {model.context_length:,} below required {int(min_ctx):,} tokens{src}")

        if hard.get("needs_vision") and not model.supports_images:
            v.append("Request contains images but model has no vision support")

        return CheckResult(passes=not v, violations=v, worst_case_latency_ms=worst)

    # ------------------------------------------------------------------
    # Stage 2: scoring
    # ------------------------------------------------------------------
    def score_models(self, models: List[ModelProfile], weights: Dict[str, float], mode: str,
                     task_distribution: Dict[str, float], expected_output_tokens: int, hard: dict,
                     reliability_of, inflight_of) -> List[RankedModel]:
        lat_ref = float(hard.get("max_latency_ms") or LATENCY_REF_MS)
        max_cost = hard.get("max_cost_per_token")
        cost_ref = max_cost if max_cost else COST_REF_PER_TOKEN
        length_factor = min(2.0, max(0.6, 0.6 + 0.4 * expected_output_tokens / TYPICAL_ANSWER_TOKENS))

        ranked = []
        for m in models:
            inflight = inflight_of(m.model_key)
            load_ratio = min(1.0, inflight / max(1, m.max_concurrency))
            expected_latency = m.avg_latency_ms * length_factor * (1 + load_ratio)
            rel = reliability_of(m.model_key, m.reliability)
            suit = sum(p * float(m.task_affinity.get(t, 0.5)) for t, p in task_distribution.items())

            f = {
                "latency": max(0.0, 1.0 - expected_latency / lat_ref),
                "capability": m.capability_score / 10.0,
                "reliability": rel,
                "task_suitability": suit,
                "cost": max(0.0, 1.0 - (m.cost_per_token / cost_ref if cost_ref else 0.0)),
                "load": 1.0 - load_ratio,
            }
            total = sum(weights[k] * f[k] for k in FACTORS)
            penalty = EXPERIMENTAL_PENALTY if (m.tier == "experimental" and mode in ("auto", "balanced")) else 0.0
            total = max(0.0, total - penalty)

            ranked.append(RankedModel(
                model_key=m.model_key,
                profile=m,
                score=round(total * 100, 2),
                score_breakdown={
                    **{f"{k}_score": round(v * 100, 1) for k, v in f.items()},
                    "weights": weights,
                    "tier_penalty": round(penalty * 100, 1),
                    "expected_latency_ms": int(expected_latency),
                    "reliability_observed": round(rel, 4),
                    "inflight": inflight,
                    "capability_0_100": round(m.capability_score * 10, 1),
                },
            ))
        ranked.sort(key=lambda r: (r.score, r.profile.capability_score), reverse=True)
        return ranked

    # ------------------------------------------------------------------
    # Request validation
    # ------------------------------------------------------------------
    def validate_constraints(self, constraints: dict) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        if not isinstance(constraints, dict):
            return False, ["constraints must be a JSON object"]

        def num(v):
            return isinstance(v, (int, float)) and not isinstance(v, bool)

        for key in ("max_latency_ms", "min_context_length", "required_context_length"):
            if constraints.get(key) is not None and (not num(constraints[key]) or constraints[key] <= 0):
                errors.append(f"'{key}' must be a positive number")
        for key in ("min_capability", "min_capability_score"):
            val = constraints.get(key)
            if val is not None and (not num(val) or not (0 <= val <= 10)):
                errors.append(f"'{key}' must be between 0 and 10")
        for key in ("max_cost_per_token", "max_cost_per_1k_tokens"):
            val = constraints.get(key)
            if val is not None and (not num(val) or val < 0):
                errors.append(f"'{key}' cannot be negative")
        pref = constraints.get("preference")
        if pref is not None:
            p = PREFERENCE_ALIASES.get(str(pref).lower(), str(pref).lower())
            if p not in PREFERENCE_WEIGHTS and p != "auto":
                errors.append(f"'preference' must be one of auto, {', '.join(PREFERENCE_WEIGHTS)}")
        return not errors, errors
