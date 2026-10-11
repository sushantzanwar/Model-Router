"""
telemetry.py - Live runtime signals for routing
------------------------------------------------
Tracks, per model:
  * in-flight requests          -> "current load" factor
  * success / failure history   -> "reliability" factor (Bayesian: configured reliability is the prior,
                                   real outcomes progressively override it)
  * measured latency (EWMA)     -> observability

Runtime history is persisted to runtime_stats.json (git-ignored), never to the judge config file.
"""

import json
import os
import tempfile
import threading
from contextlib import contextmanager
from typing import Dict

STATS_PATH = os.path.join(os.path.dirname(__file__), "runtime_stats.json")
PRIOR_STRENGTH = 20.0   # configured reliability counts as this many virtual observations
EWMA_ALPHA = 0.3


class Telemetry:
    def __init__(self, path: str = STATS_PATH, persist: bool = True):
        self._path = path
        self._persist = persist
        self._lock = threading.Lock()
        self._inflight: Dict[str, int] = {}
        self._stats: Dict[str, dict] = {}
        if persist and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._stats = json.load(f)
            except Exception:
                self._stats = {}

    def _entry(self, key: str) -> dict:
        return self._stats.setdefault(key, {"success": 0, "failure": 0, "latency_ewma_ms": None})

    @contextmanager
    def track(self, key: str):
        with self._lock:
            self._inflight[key] = self._inflight.get(key, 0) + 1
        try:
            yield
        finally:
            with self._lock:
                self._inflight[key] = max(0, self._inflight.get(key, 1) - 1)

    def inflight(self, key: str) -> int:
        with self._lock:
            return self._inflight.get(key, 0)

    def record(self, key: str, success: bool, latency_ms: int = 0):
        with self._lock:
            e = self._entry(key)
            e["success" if success else "failure"] += 1
            if success and latency_ms > 0:
                prev = e["latency_ewma_ms"]
                e["latency_ewma_ms"] = round(latency_ms if prev is None else (1 - EWMA_ALPHA) * prev + EWMA_ALPHA * latency_ms, 1)
            self._save_locked()

    def reliability(self, key: str, prior: float) -> float:
        """Posterior mean success rate: Beta(prior * k + successes, (1 - prior) * k + failures)."""
        with self._lock:
            e = self._stats.get(key, {})
            s, f = e.get("success", 0), e.get("failure", 0)
        return (prior * PRIOR_STRENGTH + s) / (PRIOR_STRENGTH + s + f)

    def snapshot(self, key: str) -> dict:
        with self._lock:
            e = dict(self._stats.get(key, {"success": 0, "failure": 0, "latency_ewma_ms": None}))
            e["inflight"] = self._inflight.get(key, 0)
        return e

    def reset(self):
        with self._lock:
            self._stats = {}
            self._save_locked()

    def _save_locked(self):
        if not self._persist:
            return
        try:
            d = os.path.dirname(os.path.abspath(self._path))
            with tempfile.NamedTemporaryFile("w", dir=d, delete=False, encoding="utf-8") as tf:
                json.dump(self._stats, tf, indent=2)
                tmp = tf.name
            os.replace(tmp, self._path)
        except Exception as exc:
            print(f"[Telemetry] could not persist runtime stats: {exc}")


telemetry = Telemetry()
