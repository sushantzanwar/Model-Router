"""
evaluate.py - Measure the routing brain on the held-out evaluation set
-----------------------------------------------------------------------
Usage (from backend/):  python -m brain.evaluate
"""

from collections import Counter
from typing import Dict

import numpy as np

import copy
import os
import sys

from .analyzer import TIER_CAPABILITY_FLOOR, TIER_COMPLEXITY_CENTER, get_analyzer
from .blind_set import BLIND_SET
from .eval_set import EVAL_SET
from .final_test_set import FINAL_TEST_SET
from .neural import TASKS, TIERS


def evaluate(verbose: bool = True, data=None, name: str = "held-out") -> Dict[str, float]:
    EVAL_SET = data if data is not None else globals()["EVAL_SET"]
    analyzer = get_analyzer()
    texts = [p for p, _, _ in EVAL_SET]
    (probs, _), _ = analyzer.predict_raw(texts)
    pred_task = [TASKS[i] for i in np.argmax(probs["task"], axis=1)]
    pred_tier = [TIERS[i] for i in np.argmax(probs["tier"], axis=1)]

    n = len(EVAL_SET)
    task_ok = sum(p == t for p, (_, t, _) in zip(pred_task, EVAL_SET))
    tier_ok = sum(p == t for p, (_, _, t) in zip(pred_tier, EVAL_SET))
    tier_near = sum(abs(TIERS.index(p) - TIERS.index(t)) <= 1 for p, (_, _, t) in zip(pred_tier, EVAL_SET))

    routing_ok, near_ok, routing_misses = _routing_agreement(analyzer, EVAL_SET)
    result = {
        "examples": n,
        "task_accuracy": round(task_ok / n, 4),
        "tier_accuracy": round(tier_ok / n, 4),
        "tier_within_one": round(tier_near / n, 4),
        "routing_accuracy": round(routing_ok / n, 4),
        "routing_near_optimal": round(near_ok / n, 4),
    }
    if verbose:
        per_task = Counter(t for _, t, _ in EVAL_SET)
        hits = Counter(t for p, (_, t, _) in zip(pred_task, EVAL_SET) if p == t)
        print(f"=== {name} set: {n} prompts ===")
        print(f"Task accuracy : {result['task_accuracy'] * 100:.1f}%")
        print(f"Tier accuracy : {result['tier_accuracy'] * 100:.1f}%  (within one tier: {result['tier_within_one'] * 100:.1f}%)")
        print(f"ROUTING accuracy (same model as the true labels would pick): {result['routing_accuracy'] * 100:.1f}%")
        print(f"Near-optimal routing (meets true needs, within {NEAR_OPTIMAL_POINTS} pts of best): {result['routing_near_optimal'] * 100:.1f}%")
        for prompt, want, got, gap in routing_misses:
            tag = f"gap {gap:.1f} pts" if gap is not None else "violates true needs"
            print(f"    routed {got} instead of {want} ({tag}) :: {prompt[:64]!r}")
        print("Per-task accuracy:")
        for t in TASKS:
            if per_task[t]:
                print(f"  {t:<14} {hits[t]}/{per_task[t]}")
        print("Misclassified:")
        for (prompt, t, tr), pt, ptr in zip(EVAL_SET, pred_task, pred_tier):
            if pt != t or ptr != tr:
                flag = ("TASK " if pt != t else "     ") + ("TIER" if ptr != tr else "")
                print(f"  [{flag:<9}] true={t}/{tr} pred={pt}/{ptr} :: {prompt[:80]!r}")
    return result


NEAR_OPTIMAL_POINTS = 2.0


def _routing_agreement(analyzer, EVAL_SET):
    """
    End-to-end check: route each held-out prompt twice under default judge settings -
    once with the brain's analysis, once with an oracle analysis built from the true labels -
    and count how often the same model is selected.
    """
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from models import ModelProfile, _DEFAULT_PROFILES
    from router import ModelRouter
    from telemetry import Telemetry

    models = {d["model_key"]: ModelProfile(**copy.deepcopy(d)) for d in _DEFAULT_PROFILES}
    router = ModelRouter(telemetry=Telemetry(persist=False))
    ok, near, misses = 0, 0, []
    for prompt, task, tier in EVAL_SET:
        predicted = analyzer.analyze(prompt)
        oracle = copy.deepcopy(predicted)
        oracle.task_distribution = {t: float(t == task) for t in TASKS}
        oracle.tier_distribution = {t: float(t == tier) for t in TIERS}
        oracle.required_capability = TIER_CAPABILITY_FLOOR[tier]
        oracle.complexity_score = TIER_COMPLEXITY_CENTER[tier]
        oracle.uncertainty = 0.0
        got = router.route(prompt, {}, models, profile=predicted)["selected"]
        truth = router.route(prompt, {}, models, profile=oracle)
        want = truth["selected"]
        scores = {c["model_key"]: c["score"] for c in truth["candidates"] if c["score"] is not None}
        gap = (scores[want] - scores[got]) if got in scores else None
        if got == want:
            ok += 1
            near += 1
        else:
            if gap is not None and gap <= NEAR_OPTIMAL_POINTS:
                near += 1
            misses.append((prompt, want, got, gap))
    return ok, near, misses


def evaluate_all() -> Dict[str, Dict[str, float]]:
    return {"final_test": evaluate(False, FINAL_TEST_SET), "held_out": evaluate(False, EVAL_SET),
            "second_set": evaluate(False, BLIND_SET)}


if __name__ == "__main__":
    evaluate(True, EVAL_SET, "held-out (tuning)")
    print()
    evaluate(True, BLIND_SET, "second (seen during tuning)")
    print()
    evaluate(True, FINAL_TEST_SET, "FINAL TEST (never tuned on)")
