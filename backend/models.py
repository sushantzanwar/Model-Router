"""
models.py - Model Registry for A-01 ModelRouter
------------------------------------------------
Official Model Catalog verified against operator's Ollama engine:
1. qwen3.5:2b   - 2.7 GB - Text & Vision - completion, thinking, tools, vision
2. qwen3.5:4b   - 3.3 GB - Text & Vision - completion, thinking, tools, vision
3. deepseek-r1:7b - 4.7 GB - Text        - completion, thinking, tools
4. gemma4:12b   - 8.0 GB - Text & Vision - audio, completion, thinking, tools, vision
5. gpt-oss:20b  - 13 GB  - Text          - completion, thinking, tools

Manages the shared model registry for:
  Pipeline A: Model Configuration (Judge parameters, SLA, latency bounds)
  Pipeline B: Runtime Model Routing (Used by router to filter and score candidates)
"""

import os
import json
import tempfile
import copy
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, List, Any, Tuple
from threading import Lock

CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), "models_config.json")


@dataclass
class ModelProfile:
    """
    Represents a single registered model and its configuration.

    Parameters:
        model_key           : Internal unique identifier (e.g. 'qwen-2b')
        name                : Display name (e.g. 'Qwen3.5 2B')
        role                : Functional role description
        avg_latency_ms      : Configured estimate of average response latency (used for ranking)
        max_latency_ms      : Configured upper-bound latency estimate (hard deadline constraint)
        measured_latency_ms : Actual latency recorded from the most recent real execution
        capability_score    : Model capability rating (1.0 to 10.0)
        context_length      : Maximum context capacity in tokens
        reliability         : Reliability score (0.0 to 1.0)
        availability        : Whether model is online/offline
        enabled             : Enabled status for routing
        cost_per_1k_tokens  : Cost in USD per 1K tokens (0.0 for local Ollama)
        provider            : 'ollama'
        model_id            : Official provider model ID (e.g. 'qwen3.5:2b', 'gemma4:12b')
        size_gb             : Model on-disk download size
        supports_images     : Vision input capability flag
        capabilities        : Capabilities reported by Ollama (completion, thinking, vision, etc.)
        description         : Detailed description
        tier                : 'stable' or 'experimental' (experimental is slightly penalised under balanced routing)
        task_affinity       : Suitability 0..1 per task type (from the model card / catalog; judge-editable)
        max_concurrency     : Requests the model can serve at once before queueing (drives the load penalty)
    """
    model_key: str
    name: str
    role: str
    avg_latency_ms: int
    max_latency_ms: int
    measured_latency_ms: int
    capability_score: float
    context_length: int
    reliability: float
    availability: bool
    enabled: bool
    cost_per_1k_tokens: float
    provider: str
    model_id: str
    size_gb: str = "3.0 GB"
    supports_images: bool = False
    capabilities: str = "completion, thinking, tools"
    description: str = ""
    tier: str = "stable"
    task_affinity: Dict[str, float] = field(default_factory=dict)
    max_concurrency: int = 2

    # Legacy/compatibility aliases
    @property
    def capability(self) -> float:
        return self.capability_score

    @property
    def latency_ms(self) -> int:
        return self.avg_latency_ms

    @property
    def cost_per_token(self) -> float:
        return self.cost_per_1k_tokens / 1000.0

    @property
    def available(self) -> bool:
        return self.availability and self.enabled

    def to_dict(self) -> dict:
        d = asdict(self)
        d["capability"] = self.capability_score
        d["latency_ms"] = self.avg_latency_ms
        d["cost_per_token"] = self.cost_per_token
        d["available"] = self.available
        return d


# ---------------------------------------------------------------------------
# Default 5 Ollama Model Profiles (Source of Truth from MODEL_CATALOG.md)
# ---------------------------------------------------------------------------
_DEFAULT_PROFILES: List[dict] = [
    {
        "model_key": "qwen-2b",
        "name": "Qwen3.5 2B",
        "role": "Lightweight tasks (Text & Vision)",
        "avg_latency_ms": 650,
        "max_latency_ms": 1800,
        "measured_latency_ms": 620,
        "capability_score": 4.5,
        "context_length": 32768,
        "reliability": 0.98,
        "availability": True,
        "enabled": True,
        "cost_per_1k_tokens": 0.0,
        "provider": "ollama",
        "model_id": "qwen3.5:2b",
        "size_gb": "2.7 GB",
        "supports_images": True,
        "capabilities": "completion, thinking, tools, vision",
        "description": "Ultra-fast 2.7GB model with vision. Ideal for short summaries and factual questions.",
        "tier": "stable",
        "max_concurrency": 3,
        "task_affinity": {'conversation': 0.95, 'factual': 0.8, 'explanation': 0.6, 'summarization': 0.7, 'translation': 0.65, 'creative': 0.6, 'coding': 0.35, 'math': 0.35, 'reasoning': 0.3, 'analysis': 0.4},
    },
    {
        "model_key": "qwen-4b",
        "name": "Qwen3.5 4B",
        "role": "General-purpose tasks (Text & Vision)",
        "avg_latency_ms": 1250,
        "max_latency_ms": 3200,
        "measured_latency_ms": 1180,
        "capability_score": 6.8,
        "context_length": 32768,
        "reliability": 0.96,
        "availability": True,
        "enabled": True,
        "cost_per_1k_tokens": 0.0,
        "provider": "ollama",
        "model_id": "qwen3.5:4b",
        "size_gb": "3.3 GB",
        "supports_images": True,
        "capabilities": "completion, thinking, tools, vision",
        "description": "Everyday balanced 3.3GB model with vision. Balances speed, context, and quality.",
        "tier": "stable",
        "max_concurrency": 3,
        "task_affinity": {'conversation': 0.9, 'factual': 0.85, 'explanation': 0.8, 'summarization': 0.85, 'translation': 0.8, 'creative': 0.75, 'coding': 0.6, 'math': 0.6, 'reasoning': 0.55, 'analysis': 0.7},
    },
    {
        "model_key": "deepseek-r1",
        "name": "DeepSeek-R1 7B",
        "role": "Reasoning and mathematics",
        "avg_latency_ms": 2800,
        "max_latency_ms": 7500,
        "measured_latency_ms": 2740,
        "capability_score": 8.9,
        "context_length": 65536,
        "reliability": 0.94,
        "availability": True,
        "enabled": True,
        "cost_per_1k_tokens": 0.0,
        "provider": "ollama",
        "model_id": "deepseek-r1:7b",
        "size_gb": "4.7 GB",
        "supports_images": False,
        "capabilities": "completion, thinking, tools",
        "description": "Deep 4.7GB chain-of-thought model. Excels at formal proofs, logic, and mathematics.",
        "tier": "stable",
        "max_concurrency": 2,
        "task_affinity": {'conversation': 0.4, 'factual': 0.7, 'explanation': 0.8, 'summarization': 0.6, 'translation': 0.5, 'creative': 0.45, 'coding': 0.8, 'math': 0.98, 'reasoning': 0.98, 'analysis': 0.85},
    },
    {
        "model_key": "gemma-12b",
        "name": "Gemma 4 12B",
        "role": "Image understanding, OCR, and document parsing",
        "avg_latency_ms": 3400,
        "max_latency_ms": 8200,
        "measured_latency_ms": 3310,
        "capability_score": 8.2,
        "context_length": 131072,
        "reliability": 0.95,
        "availability": True,
        "enabled": True,
        "cost_per_1k_tokens": 0.0,
        "provider": "ollama",
        "model_id": "gemma4:12b",
        "size_gb": "8.0 GB",
        "supports_images": True,
        "capabilities": "audio, completion, thinking, tools, vision",
        "description": "Multimodal 8.0GB architecture with native vision & document extraction.",
        "tier": "stable",
        "max_concurrency": 2,
        "task_affinity": {'conversation': 0.75, 'factual': 0.85, 'explanation': 0.85, 'summarization': 0.92, 'translation': 0.9, 'creative': 0.85, 'coding': 0.7, 'math': 0.7, 'reasoning': 0.75, 'analysis': 0.88},
    },
    {
        "model_key": "gpt-oss-20b",
        "name": "GPT-OSS 20B",
        "role": "Advanced reasoning and coding",
        "avg_latency_ms": 4200,
        "max_latency_ms": 9500,
        "measured_latency_ms": 4150,
        "capability_score": 9.4,
        "context_length": 131072,
        "reliability": 0.92,
        "availability": True,
        "enabled": True,
        "cost_per_1k_tokens": 0.0,
        "provider": "ollama",
        "model_id": "gpt-oss:20b",
        "size_gb": "13 GB",
        "supports_images": False,
        "capabilities": "completion, thinking, tools",
        "description": "High-capacity 13GB coding engine for complex software architecture and debugging.",
        "tier": "experimental",
        "max_concurrency": 1,
        "task_affinity": {'conversation': 0.6, 'factual': 0.85, 'explanation': 0.9, 'summarization': 0.8, 'translation': 0.75, 'creative': 0.8, 'coding': 0.98, 'math': 0.88, 'reasoning': 0.92, 'analysis': 0.92},
    },
]


class ModelRegistry:
    """
    Shared model registry supporting atomic persistence, thread safety,
    and validation for Judge Model Configuration & Routing.
    """

    ALLOWED_UPDATE_FIELDS = {
        "avg_latency_ms": (int, float),
        "max_latency_ms": (int, float),
        "capability_score": (int, float),
        "context_length": (int, float),
        "reliability": (int, float),
        "availability": bool,
        "enabled": bool,
        "cost_per_1k_tokens": (int, float),
        "tier": str,
        "task_affinity": dict,
        "max_concurrency": int,
        # Legacy/UI alias support
        "latency_ms": (int, float),
        "capability": (int, float),
        "available": bool,
    }

    def __init__(self, persistence_path: str = CONFIG_FILE_PATH):
        self._persistence_path = persistence_path
        self._lock = Lock()
        self._store: Dict[str, ModelProfile] = {}
        self._init_store()

    def _init_store(self):
        """Load from persistent JSON file if exists and valid, otherwise load defaults."""
        if os.path.exists(self._persistence_path):
            try:
                with open(self._persistence_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    self._store = {}
                    for item in data:
                        # Normalize aliases
                        if "capability_score" not in item and "capability" in item:
                            item["capability_score"] = item["capability"]
                        if "avg_latency_ms" not in item and "latency_ms" in item:
                            item["avg_latency_ms"] = item["latency_ms"]
                        if "max_latency_ms" not in item:
                            item["max_latency_ms"] = item.get("avg_latency_ms", 3000) * 2
                        if "measured_latency_ms" not in item:
                            item["measured_latency_ms"] = item.get("avg_latency_ms", 1000)
                        if "reliability" not in item:
                            item["reliability"] = 0.95
                        if "cost_per_1k_tokens" not in item:
                            item["cost_per_1k_tokens"] = 0.0
                        if "enabled" not in item:
                            item["enabled"] = True
                        if "role" not in item:
                            item["role"] = "General task"

                        # Fill fields added in newer versions from the canonical defaults
                        defaults = next((d for d in _DEFAULT_PROFILES if d["model_key"] == item.get("model_key")), {})
                        for fld in ("tier", "task_affinity", "max_concurrency", "supports_images", "capabilities"):
                            if fld not in item and fld in defaults:
                                item[fld] = copy.deepcopy(defaults[fld])

                        # Strip non-dataclass keys if any
                        clean_item = {
                            k: v for k, v in item.items()
                            if k in ModelProfile.__annotations__
                        }
                        self._store[clean_item["model_key"]] = ModelProfile(**clean_item)
                    return
            except Exception as e:
                print(f"[ModelRegistry] Error reading {self._persistence_path}: {e}. Falling back to defaults.")

        self._load_defaults_locked()

    def _load_defaults_locked(self):
        self._store = {}
        for spec in _DEFAULT_PROFILES:
            self._store[spec["model_key"]] = ModelProfile(**spec)
        self._save_to_disk_locked()

    def _save_to_disk_locked(self):
        """Atomically persist configuration to disk."""
        try:
            abs_path = os.path.abspath(self._persistence_path)
            dir_name = os.path.dirname(abs_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            data = [asdict(p) for p in self._store.values()]
            with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
                json.dump(data, tf, indent=2)
                temp_name = tf.name
            os.replace(temp_name, abs_path)
        except Exception as e:
            print(f"[ModelRegistry] Failed to persist config to disk: {e}")

    def get_all(self) -> Dict[str, ModelProfile]:
        with self._lock:
            return {k: copy.deepcopy(v) for k, v in self._store.items()}

    def get(self, model_key: str) -> Optional[ModelProfile]:
        with self._lock:
            profile = self._store.get(model_key)
            return copy.deepcopy(profile) if profile else None

    def exists(self, model_key: str) -> bool:
        with self._lock:
            return model_key in self._store

    def validate_patch(self, updates: dict) -> Tuple[bool, Optional[str]]:
        """Validate candidate patch fields and value bounds."""
        for key, val in updates.items():
            if key not in self.ALLOWED_UPDATE_FIELDS:
                return False, f"Unknown configuration field: '{key}'"

            expected_type = self.ALLOWED_UPDATE_FIELDS[key]
            if not isinstance(val, expected_type):
                return False, f"Invalid type for field '{key}': expected {expected_type}, got {type(val)}"

            # Value range validations
            if key in ("avg_latency_ms", "max_latency_ms", "latency_ms") and val <= 0:
                return False, f"'{key}' must be positive integer (> 0)"
            if key in ("capability_score", "capability") and not (1.0 <= val <= 10.0):
                return False, f"'{key}' must be between 1.0 and 10.0"
            if key == "reliability" and not (0.0 <= val <= 1.0):
                return False, "'reliability' must be between 0.0 and 1.0"
            if key == "cost_per_1k_tokens" and val < 0:
                return False, "'cost_per_1k_tokens' cannot be negative"
            if key == "context_length" and val < 128:
                return False, "'context_length' must be at least 128 tokens"
            if key == "tier" and val not in ("stable", "experimental"):
                return False, "'tier' must be 'stable' or 'experimental'"
            if key == "max_concurrency" and not (1 <= val <= 64):
                return False, "'max_concurrency' must be between 1 and 64"
            if key == "task_affinity":
                from brain.neural import TASKS
                for t, a in val.items():
                    if t not in TASKS:
                        return False, f"Unknown task '{t}' in task_affinity (valid: {', '.join(TASKS)})"
                    if not isinstance(a, (int, float)) or not (0.0 <= a <= 1.0):
                        return False, f"task_affinity['{t}'] must be between 0.0 and 1.0"

        return True, None

    def update(self, model_key: str, updates: dict) -> Tuple[Optional[ModelProfile], Optional[str]]:
        """
        Validate and update model configuration. Persists atomically.
        Returns (updated_profile, error_message).
        """
        with self._lock:
            profile = self._store.get(model_key)
            if not profile:
                return None, f"Model '{model_key}' not found."

            valid, err = self.validate_patch(updates)
            if not valid:
                return None, err

            for key, val in updates.items():
                if key == "latency_ms":
                    profile.avg_latency_ms = int(val)
                elif key == "avg_latency_ms":
                    profile.avg_latency_ms = int(val)
                elif key == "max_latency_ms":
                    profile.max_latency_ms = int(val)
                elif key in ("capability_score", "capability"):
                    profile.capability_score = float(val)
                elif key == "context_length":
                    profile.context_length = int(val)
                elif key == "reliability":
                    profile.reliability = float(val)
                elif key == "availability":
                    profile.availability = bool(val)
                elif key == "available":
                    profile.availability = bool(val)
                    profile.enabled = bool(val)
                elif key == "enabled":
                    profile.enabled = bool(val)
                elif key == "cost_per_1k_tokens":
                    profile.cost_per_1k_tokens = float(val)
                elif key == "tier":
                    profile.tier = val
                elif key == "max_concurrency":
                    profile.max_concurrency = int(val)
                elif key == "task_affinity":
                    profile.task_affinity = {**profile.task_affinity, **{t: float(a) for t, a in val.items()}}

            self._save_to_disk_locked()
            return copy.deepcopy(profile), None

    def record_measured_latency(self, model_key: str, measured_ms: int):
        """Update actual measured execution latency (runtime only - judge configuration file is untouched)."""
        with self._lock:
            profile = self._store.get(model_key)
            if profile:
                profile.measured_latency_ms = int(measured_ms)

    def reset(self) -> List[dict]:
        """Reset all model profiles to canonical defaults."""
        with self._lock:
            self._load_defaults_locked()
            return [p.to_dict() for p in self._store.values()]

    def to_list(self) -> List[dict]:
        with self._lock:
            return [p.to_dict() for p in self._store.values()]


# Module singleton
registry = ModelRegistry()
