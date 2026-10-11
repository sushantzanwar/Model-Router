"""
analyzer.py - PromptAnalyzer: turns raw text into routing requirements
-----------------------------------------------------------------------
Runs the trained neural ensemble and converts its probability outputs into a
PromptProfile - the concrete requirements a model must meet for this prompt:

  * task distribution            -> task-suitability matching against each model
  * complexity tier distribution -> required capability (with an uncertainty margin:
                                    when the network is unsure, it asks for MORE capability)
  * answer-length distribution   -> expected output tokens -> required context window
  * attachments                  -> vision requirement
"""

import hashlib
import math
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .features import STRUCT_LABELS, STRUCT_NAMES, encode
from .neural import LENGTHS, TASKS, TIERS, Ensemble, train_ensemble

MODEL_VERSION = "brain-v1"
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
CACHE_PATH = os.path.join(CACHE_DIR, "brain_weights.npz")

# Capability (1-10 scale) a model needs to handle each complexity tier reliably.
TIER_CAPABILITY_FLOOR = {"simple": 3.0, "moderate": 4.5, "complex": 6.5, "expert": 8.0}
# Position of each tier on the 1-10 complexity scale shown to users.
TIER_COMPLEXITY_CENTER = {"simple": 2.0, "moderate": 4.5, "complex": 7.0, "expert": 9.2}
# Typical answer size in tokens for each length class.
LENGTH_TOKENS = {"short": 150, "medium": 450, "long": 1100}
SYSTEM_OVERHEAD_TOKENS = 300
UNCERTAINTY_MARGIN = 0.8  # fraction of the gap to the next tier added when the network is maximally unsure

TIER_LABEL = {"simple": "SIMPLE", "moderate": "MODERATE", "complex": "COMPLEX", "expert": "REASONING_INTENSIVE"}


@dataclass
class PromptProfile:
    task: str
    task_confidence: float
    task_distribution: Dict[str, float]
    secondary_task: Optional[str]
    tier: str
    tier_distribution: Dict[str, float]
    complexity_score: float
    label: str
    uncertainty: float
    required_capability: float
    estimated_prompt_tokens: int
    expected_output_tokens: int
    required_context_tokens: int
    needs_vision: bool
    signals: List[str] = field(default_factory=list)
    explanation: str = ""
    analysis_ms: float = 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        # Fields consumed by the existing frontend
        d["score"] = self.complexity_score
        d["inferred_min_capability"] = self.required_capability
        return d


def _entropy(p: np.ndarray) -> float:
    p = np.clip(p, 1e-9, 1.0)
    return float(-(p * np.log(p)).sum() / math.log(len(p)))


class PromptAnalyzer:
    def __init__(self, log=print):
        self._log = log
        self._lock = threading.Lock()
        self._model: Optional[Ensemble] = None
        self._train_stats: dict = {}

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------
    @staticmethod
    def _fingerprint(corpus) -> str:
        h = hashlib.sha1(MODEL_VERSION.encode())
        for text, task, tier, length in corpus:
            h.update(f"{text}\x1f{task}\x1f{tier}\x1f{length}\x1e".encode("utf-8"))
        return h.hexdigest()

    def ensure_ready(self) -> Ensemble:
        if self._model is not None:
            return self._model
        with self._lock:
            if self._model is not None:
                return self._model
            from .corpus import build_corpus
            corpus = build_corpus()
            fp = self._fingerprint(corpus)
            if os.path.exists(CACHE_PATH):
                try:
                    model = Ensemble.load(CACHE_PATH, fp)
                    if model is not None:
                        self._model = model
                        self._train_stats = {"source": "cache", "examples": len(corpus)}
                        return model
                except Exception as exc:  # corrupt cache -> retrain
                    self._log(f"[brain] cache unreadable ({exc}); retraining")
            self._model = self._train(corpus, fp)
            return self._model

    def _train(self, corpus, fp: str) -> Ensemble:
        t0 = time.time()
        self._log(f"[brain] training neural router on {len(corpus)} labelled examples ...")
        encoded = [encode(t) for t, _, _, _ in corpus]
        labels = {
            "task": np.array([TASKS.index(c[1]) for c in corpus]),
            "tier": np.array([TIERS.index(c[2]) for c in corpus]),
            "length": np.array([LENGTHS.index(c[3]) for c in corpus]),
        }
        model = train_ensemble(encoded, labels, log=self._log)
        os.makedirs(CACHE_DIR, exist_ok=True)
        model.save(CACHE_PATH, fp)
        secs = round(time.time() - t0, 1)
        self._train_stats = {"source": "trained", "examples": len(corpus), "train_seconds": secs}
        self._log(f"[brain] training complete in {secs}s (cached to {CACHE_PATH})")
        return model

    @property
    def info(self) -> dict:
        self.ensure_ready()
        return {
            "version": MODEL_VERSION,
            "architecture": "ensemble of 3 embedding-bag neural networks (hashed subwords + structural signals)",
            "tasks": TASKS,
            "tiers": TIERS,
            **self._train_stats,
        }

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    def predict_raw(self, texts: List[str]):
        model = self.ensure_ready()
        enc = [encode(t) for t in texts]
        return model.predict([e[0] for e in enc], [e[1] for e in enc], np.stack([e[2] for e in enc])), enc

    def analyze(self, prompt: str, has_images: bool = False) -> PromptProfile:
        t0 = time.perf_counter()
        (probs, spread), enc = self.predict_raw([prompt])
        model = self._model
        task_p, tier_p, len_p = probs["task"][0], probs["tier"][0], probs["length"][0]

        order = np.argsort(-task_p)
        task = TASKS[order[0]]
        secondary = TASKS[order[1]] if task_p[order[1]] >= 0.2 else None
        tier = TIERS[int(np.argmax(tier_p))]

        # Uncertainty: entropy of the tier/task beliefs + disagreement between ensemble members.
        uncertainty = float(np.clip(
            0.45 * _entropy(tier_p) + 0.25 * _entropy(task_p)
            + 0.15 * float(spread["tier"][0]) + 0.15 * float(spread["task"][0]), 0.0, 1.0))

        # Robust requirement: floor of the median tier, plus an uncertainty margin toward the next tier up.
        # (A mean would let a thin tail of probability on 'expert' veto every small model.)
        median_idx = int(np.searchsorted(np.cumsum(tier_p), 0.5))
        median_idx = min(median_idx, len(TIERS) - 1)
        floor = TIER_CAPABILITY_FLOOR[TIERS[median_idx]]
        next_floor = TIER_CAPABILITY_FLOOR[TIERS[min(median_idx + 1, len(TIERS) - 1)]]
        margin = UNCERTAINTY_MARGIN * uncertainty * (next_floor - floor if next_floor > floor else 1.0)
        required_cap = round(min(10.0, floor + margin), 1)
        complexity = round(sum(float(tier_p[i]) * TIER_COMPLEXITY_CENTER[t] for i, t in enumerate(TIERS)), 1)

        prompt_tokens = max(1, math.ceil(len(prompt) / 4))
        out_tokens = int(round(sum(float(len_p[i]) * LENGTH_TOKENS[l] for i, l in enumerate(LENGTHS))))
        ctx = prompt_tokens + out_tokens + SYSTEM_OVERHEAD_TOKENS

        signals = self._signals(enc[0][2], model)
        task_dist = {t: round(float(task_p[i]), 4) for i, t in enumerate(TASKS)}
        tier_dist = {t: round(float(tier_p[i]), 4) for i, t in enumerate(TIERS)}

        explanation = (
            f"Neural analysis: {task} request ({task_p[order[0]] * 100:.0f}% confidence"
            + (f", also {secondary} {task_p[order[1]] * 100:.0f}%" if secondary else "")
            + f"), {tier} complexity ({tier_p.max() * 100:.0f}%). "
            f"Needs capability >= {required_cap}/10"
            + (f" (includes +{margin:.1f} safety margin for uncertainty {uncertainty:.2f})" if margin >= 0.05 else "")
            + f", ~{prompt_tokens} prompt + ~{out_tokens} answer tokens."
        )

        return PromptProfile(
            task=task,
            task_confidence=round(float(task_p[order[0]]), 4),
            task_distribution=task_dist,
            secondary_task=secondary,
            tier=tier,
            tier_distribution=tier_dist,
            complexity_score=max(1.0, min(10.0, complexity)),
            label=TIER_LABEL[tier],
            uncertainty=round(uncertainty, 3),
            required_capability=required_cap,
            estimated_prompt_tokens=prompt_tokens,
            expected_output_tokens=out_tokens,
            required_context_tokens=ctx,
            needs_vision=bool(has_images),
            signals=signals,
            explanation=explanation,
            analysis_ms=round((time.perf_counter() - t0) * 1000, 2),
        )

    @staticmethod
    def _signals(struct: np.ndarray, model: Ensemble, top: int = 4) -> List[str]:
        """Most unusual structural properties of this prompt relative to the training distribution."""
        z = (struct - model.mu) / model.sigma
        idx = np.argsort(-np.abs(z))[:top]
        out = []
        for i in idx:
            if abs(z[i]) < 1.0:
                continue
            name = STRUCT_NAMES[i]
            out.append(f"{'high' if z[i] > 0 else 'low'} {STRUCT_LABELS[name]} (z={z[i]:+.1f})")
        return out


_singleton: Optional[PromptAnalyzer] = None
_singleton_lock = threading.Lock()


def get_analyzer() -> PromptAnalyzer:
    global _singleton
    if _singleton is None:
        with _singleton_lock:
            if _singleton is None:
                _singleton = PromptAnalyzer()
    return _singleton
