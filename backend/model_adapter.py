"""
model_adapter.py - Local Ollama execution layer for A-01 ModelRouter
---------------------------------------------------------------------
Runs the model the router selected on the local Ollama daemon (models installed on this
machine). No external/cloud API is used, and the adapter never substitutes a different
model: if the selected model cannot run, it reports a failure so the gateway can fail over
to the next model that satisfies every constraint.
"""

import os
import time
from typing import List, Optional

import requests

from models import ModelProfile, registry

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT_SECONDS", "180"))
MIN_PREDICT, MAX_PREDICT = 128, 1024

MODEL_SYSTEM_PROMPTS = {
    "qwen-2b": "You are Qwen3.5 2B, an ultra-fast, lightweight, concise AI assistant. Answer directly and concisely.",
    "qwen-4b": "You are Qwen3.5 4B, a versatile and balanced general-purpose AI assistant. Provide clear, well-structured answers.",
    "deepseek-r1": "You are DeepSeek-R1 7B, an elite reasoning and mathematics model. Provide clear step-by-step reasoning, logical deductions, and thoroughly verified solutions.",
    "gpt-oss-20b": "You are GPT-OSS 20B, a high-capacity AI specialized in software engineering, complex systems, and advanced coding. Provide detailed, production-grade solutions and explanations.",
    "gemma-12b": "You are Gemma 4 12B, an advanced multimodal and structured analytical AI. Provide clear, structured, and comprehensive analytical responses.",
}


class ModelAdapter:
    def call_model(self, profile: ModelProfile, prompt: str, expected_output_tokens: int = 450,
                   images: Optional[List[str]] = None) -> dict:
        payload = {
            "model": profile.model_id,
            "prompt": prompt,
            "system": MODEL_SYSTEM_PROMPTS.get(profile.model_key, ""),
            "stream": False,
            "options": {
                "num_predict": int(min(MAX_PREDICT, max(MIN_PREDICT, expected_output_tokens * 1.3))),
                "temperature": 0.7,
            },
        }
        if images:
            payload["images"] = images

        start = time.time()
        try:
            resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=OLLAMA_TIMEOUT_S)
            elapsed_ms = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                data = resp.json()
                text = (data.get("response") or "").strip()
                if text:
                    registry.record_measured_latency(profile.model_key, elapsed_ms)
                    return self._ok(text, elapsed_ms, data.get("eval_count", max(1, len(text) // 4)))
                return self._fail(f"Model '{profile.model_id}' returned an empty response.", elapsed_ms)
            detail = ""
            try:
                detail = resp.json().get("error", "")
            except Exception:
                detail = resp.text[:200]
            if resp.status_code == 404:
                return self._fail(f"Model '{profile.model_id}' is not installed in local Ollama ({detail}).", elapsed_ms)
            return self._fail(f"Ollama HTTP {resp.status_code} for '{profile.model_id}': {detail}", elapsed_ms)
        except requests.Timeout:
            return self._fail(f"Model '{profile.model_id}' timed out after {OLLAMA_TIMEOUT_S:.0f}s.",
                              int((time.time() - start) * 1000))
        except requests.ConnectionError:
            return self._fail(f"Local Ollama is not reachable at {OLLAMA_URL}. Start the Ollama app or run 'ollama serve'.",
                              int((time.time() - start) * 1000))

    @staticmethod
    def _ok(text: str, latency_ms: int, tokens: int) -> dict:
        return {"text": text, "latency_ms": latency_ms, "tokens_used": tokens, "success": True,
                "error": None, "simulated": False, "execution_mode": "REAL_OLLAMA_LOCAL"}

    @staticmethod
    def _fail(error: str, latency_ms: int) -> dict:
        return {"text": "", "latency_ms": latency_ms, "tokens_used": 0, "success": False,
                "error": error, "simulated": False, "execution_mode": "EXECUTION_ERROR"}
