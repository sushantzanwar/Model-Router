"""
test_router_pipelines.py - Automated Tests for Pipeline A (Configuration) & Pipeline B (Routing)
------------------------------------------------------------------------------------------------
Pipeline A: registry defaults, validation, persistence, reset
Pipeline B (judge scenarios): Tests A-E from the challenge brief
Neural routing: prompt-derived requirements, judge sliders, load, reliability, cost, vision
Brain quality: accuracy floor on the blind test set
"""

import os
import unittest

from brain import get_analyzer
from models import ModelRegistry
from router import ModelRouter
from telemetry import Telemetry


class RouterTestBase(unittest.TestCase):
    def setUp(self):
        self.test_json = "test_models_config.json"
        if os.path.exists(self.test_json):
            os.remove(self.test_json)
        self.registry = ModelRegistry(persistence_path=self.test_json)
        self.telemetry = Telemetry(persist=False)
        self.router = ModelRouter(telemetry=self.telemetry)

    def tearDown(self):
        if os.path.exists(self.test_json):
            os.remove(self.test_json)

    def route(self, prompt, constraints=None, **kw):
        return self.router.route(prompt, constraints or {}, self.registry.get_all(), **kw)


class TestPipelineA(RouterTestBase):
    def test_01_registry_defaults(self):
        models = self.registry.get_all()
        self.assertEqual(set(models), {"qwen-2b", "qwen-4b", "deepseek-r1", "gemma-12b", "gpt-oss-20b"})
        self.assertEqual(models["qwen-2b"].avg_latency_ms, 650)
        self.assertEqual(models["qwen-2b"].max_latency_ms, 1800)
        self.assertEqual(models["gpt-oss-20b"].tier, "experimental")
        self.assertGreater(models["deepseek-r1"].task_affinity["math"], 0.9)

    def test_02_patch_validation_invalid_values(self):
        for bad in ({"avg_latency_ms": -100}, {"capability_score": 15.0}, {"hack_field": "exploit"},
                    {"tier": "legendary"}, {"task_affinity": {"cooking": 0.5}}, {"task_affinity": {"math": 2}}):
            valid, _ = self.registry.validate_patch(bad)
            self.assertFalse(valid, bad)

    def test_03_persistence_of_judge_changes(self):
        updated, err = self.registry.update("qwen-2b", {"avg_latency_ms": 1900, "enabled": True})
        self.assertIsNone(err)
        self.assertEqual(updated.avg_latency_ms, 1900)
        reloaded = ModelRegistry(persistence_path=self.test_json).get("qwen-2b")
        self.assertEqual(reloaded.avg_latency_ms, 1900)


class TestJudgeScenarios(RouterTestBase):
    CONSTRAINTS = {"max_latency_ms": 4000, "min_capability_score": 3, "required_context_length": 1000,
                   "preference": "lowest_latency"}

    def test_04_test_a_normal_request(self):
        """TEST A: 'HII' under a 4s budget -> fastest eligible model, Qwen3.5 2B."""
        decision = self.route("HII", self.CONSTRAINTS)
        self.assertEqual(decision["status"], "SUCCESS")
        self.assertEqual(decision["selected"], "qwen-2b")

    def test_05_test_b_judge_increases_latency(self):
        """TEST B: judge raises Qwen3.5 2B avg latency 650 -> 5000ms; next request goes to Qwen3.5 4B."""
        self.registry.update("qwen-2b", {"avg_latency_ms": 5000})
        decision = self.route("HII", self.CONSTRAINTS)
        self.assertEqual(decision["selected"], "qwen-4b")

    def test_06_test_c_model_disabled(self):
        """TEST C: judge disables Qwen3.5 2B -> rejected, Qwen3.5 4B selected."""
        self.registry.update("qwen-2b", {"enabled": False})
        decision = self.route("HII", self.CONSTRAINTS)
        self.assertEqual(decision["selected"], "qwen-4b")
        rejected = {c["model_key"]: c for c in decision["candidates"] if c["status"] == "rejected"}
        self.assertIn("disabled", rejected["qwen-2b"]["rejection_reason"])

    def test_07_test_d_impossible_constraints(self):
        """TEST D: impossible SLA -> NO_VALID_MODEL, never a constraint-violating model."""
        decision = self.route("Complex task", {"max_latency_ms": 100, "min_capability_score": 10.0})
        self.assertEqual(decision["status"], "NO_VALID_MODEL")
        self.assertIsNone(decision["selected"])

    def test_08_test_e_reset_defaults(self):
        """TEST E: reset restores canonical state."""
        self.registry.update("qwen-2b", {"avg_latency_ms": 8888, "enabled": False})
        self.registry.reset()
        qwen = self.registry.get("qwen-2b")
        self.assertEqual(qwen.avg_latency_ms, 650)
        self.assertTrue(qwen.enabled)


class TestNeuralRouting(RouterTestBase):
    def test_09_judge_sliders_are_hard_constraints(self):
        """Max Latency 8200ms, Min Capability 8.2, Min Context 128K -> only Gemma 4 12B qualifies."""
        decision = self.route("hello there", {"max_latency_ms": 8200, "max_cost_per_token": 0.0,
                                              "min_capability": 8.2, "min_context_length": 131072})
        self.assertEqual(decision["selected"], "gemma-12b")
        for c in decision["candidates"]:
            if c["model_key"] != "gemma-12b":
                self.assertEqual(c["status"], "rejected")

    def test_10_greeting_goes_to_small_fast_model(self):
        self.assertEqual(self.route("hey, how are you doing?")["selected"], "qwen-2b")

    def test_11_proof_needs_high_capability(self):
        decision = self.route("Prove that there are infinitely many primes of the form 6k + 5.")
        self.assertEqual(decision["analysis"]["task"], "math")
        chosen = self.registry.get(decision["selected"])
        self.assertGreaterEqual(chosen.capability_score, 8.0)
        self.assertEqual(decision["selected"], "deepseek-r1")

    def test_12_prompt_requirement_beats_permissive_judge(self):
        """Judge allows capability >= 1, but a hard prompt still demands a strong model."""
        decision = self.route("Design and implement a distributed transactional key-value store with Raft "
                              "replication, MVCC and crash recovery in Rust.", {"min_capability": 1})
        self.assertGreater(decision["effective_constraints"]["min_capability"], 6.0)
        self.assertIn(decision["selected"], ("gpt-oss-20b", "deepseek-r1"))

    def test_13_load_queueing_breaks_latency_budget(self):
        """A saturated model's queue-adjusted worst case can exceed the judge's latency budget."""
        with self.telemetry.track("qwen-2b"), self.telemetry.track("qwen-2b"), self.telemetry.track("qwen-2b"):
            decision = self.route("hi", {"max_latency_ms": 3400})
        reasons = {c["model_key"]: c["rejection_reason"] for c in decision["candidates"]}
        self.assertIn("queue", reasons["qwen-2b"] or "")
        self.assertEqual(decision["selected"], "qwen-4b")

    def test_14_observed_failures_lower_reliability(self):
        for _ in range(40):
            self.telemetry.record("qwen-2b", success=False)
        self.assertLess(self.telemetry.reliability("qwen-2b", 0.98), 0.5)
        self.assertEqual(self.route("hello!")["selected"], "qwen-4b")

    def test_15_cost_ceiling(self):
        self.registry.update("qwen-2b", {"cost_per_1k_tokens": 0.5})
        decision = self.route("hi", {"max_cost_per_token": 0.0001})
        reasons = {c["model_key"]: c["rejection_reason"] for c in decision["candidates"]}
        self.assertIn("Cost", reasons["qwen-2b"] or "")
        self.assertNotEqual(decision["selected"], "qwen-2b")

    def test_16_images_require_vision(self):
        decision = self.route("What is in this picture?", has_images=True)
        rejected = {c["model_key"] for c in decision["candidates"] if c["status"] == "rejected"}
        self.assertTrue({"deepseek-r1", "gpt-oss-20b"} <= rejected)
        self.assertTrue(self.registry.get(decision["selected"]).supports_images)

    def test_17_decision_is_explainable(self):
        decision = self.route("Compare PostgreSQL and MongoDB for an analytics workload.")
        winner = next(c for c in decision["candidates"] if c["status"] == "selected")
        for f in ("latency_score", "capability_score", "reliability_score", "task_suitability_score",
                  "cost_score", "load_score"):
            self.assertIn(f, winner["score_breakdown"])
        self.assertAlmostEqual(sum(decision["weights"].values()), 1.0, places=2)
        self.assertTrue(decision["explanation"])


class TestBrainQuality(unittest.TestCase):
    def test_18_blind_set_accuracy(self):
        from brain.blind_set import BLIND_SET
        from brain.evaluate import evaluate
        get_analyzer().ensure_ready()
        result = evaluate(verbose=False, data=BLIND_SET)
        self.assertGreaterEqual(result["task_accuracy"], 0.90)
        self.assertGreaterEqual(result["routing_accuracy"], 0.85)


if __name__ == "__main__":
    unittest.main()
