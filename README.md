# ⚡ ModelRouter — Cost-, Latency- & Quality-Aware AI Inference Gateway

**Domain 2: AI Systems & Infrastructure (Challenge A-01)**

An intelligent inference gateway that dynamically routes incoming requests to the optimal AI model based on **hard constraints** (latency, cost, capability, context length), with **explainable routing decisions** and **constraint-preserving failover**.

---

## 🎯 Problem Statement & Requirements

| Requirement | Implementation in ModelRouter |
| :--- | :--- |
| **Hard Constraints** | Maximum latency, maximum cost, minimum capability, and required context length are strictly non-negotiable. Any candidate violating even one constraint is **rejected immediately**. |
| **Explainable Decisions** | Every routing decision provides an exhaustive evaluation matrix: candidates evaluated, pass/fail checks, mathematical score breakdown, and explanation of why the winner was chosen. |
| **Constraint-Preserving Failover** | Treats endpoints as unreliable. When a primary model fails or breaches SLA, the gateway cascades down the priority queue **only** to models that satisfy all initial hard constraints. Constraints are never relaxed. |
| **No-Violation Safety** | If no registered model satisfies the requested SLA, the gateway returns a clear, explicit rejection (`NO_VALID_MODEL`) rather than dispatching to an ineligible model. |
| **Uncertainty Protection** | Query complexity and task suitability are continuously evaluated from prompt semantics and structural features with an uncertainty safety factor; when confidence is low, the router promotes to a safer capability tier. |
| **Judge Runtime Controls** | Judges can interactively modify any model's latency, availability, reliability, or load in real time and observe instantaneous routing adaptations without service restarts. |

---

## 🧠 Model Portfolio

ModelRouter manages a diverse portfolio of local & simulated models with distinct cost, speed, and capability profiles:

| Model | Key Role | Capability (1-10) | Context Window | Avg / Max Latency | Reliability | Cost / 1k Tokens |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Qwen3.5 2B** | Fast fact retrieval, simple chat | 3/10 | 4,096 | 650ms / 1,800ms | 96% | $0.00020 |
| **Qwen3.5 4B** | Balanced everyday tasks & QA | 5/10 | 8,192 | 1,250ms / 3,200ms | 94% | $0.00040 |
| **DeepSeek-R1 7B** | Complex reasoning, logic & math | 8/10 | 16,384 | 2,800ms / 7,500ms | 91% | $0.00070 |
| **Gemma 4 12B** | Extended context & deep analysis | 7/10 | 32,768 | 3,400ms / 8,200ms | 93% | $0.00085 |
| **GPT-OSS 20B** | High-capacity reasoning candidate | 9/10 | 32,768 | 4,600ms / 11,500ms | 89% | $0.00120 |

> **Hybrid Execution Engine**: If local Ollama models are running, the gateway dispatches real-time inference. When models are not downloaded locally, it gracefully executes high-fidelity persona simulation and real-time latency emulation to allow full judging of all routing pipelines.

---

## ⚙️ Routing Logic & Prioritized Parameters

Candidate models are scored and prioritized based on:
1. **Latency SLA Budget** *(Essential)*: Worst-case bounded latency evaluated against user SLA.
2. **Capability Score** *(Essential)*: Evaluated against minimum threshold & inferred query complexity.
3. **Context Length** *(Essential)*: Guarantees prompt tokens + estimated response fit within the model window.
4. **Availability** *(Essential)*: Validates runtime endpoint online and enabled status.
5. **Task Suitability** *(Highly useful)*: Semantic affinity matching (coding, math, reasoning, translation, creative writing).
6. **Observed Reliability** *(Highly useful)*: Rolling uptime weight incorporated into composite ranking.
7. **Current Load** *(Useful)*: Real-time concurrency penalty to mitigate queue saturation.
8. **Cost Efficiency** *(Useful)*: Ceiling constraint and cost factor ranking.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Start Backend Gateway
```bash
cd backend
pip install -r requirements.txt
python gateway.py
```
* The backend gateway starts on **`http://localhost:5000`**.
* Health check: `http://localhost:5000/api/health`

### 2. Start Frontend UI
```bash
cd frontend
npm install
npm run dev
```
* Open **`http://localhost:3000`** in your browser.
* Built with React 18, TypeScript, Vite, and custom glassmorphism design.

---

## 🧪 Automated Test Suite

Run the full automated test suite verifying Model Configuration (Pipeline A), Runtime Routing (Pipeline B), Judge Controls, and Failover:

```bash
cd backend
python test_router_pipelines.py
```

### Included Tests:
- `test_01_registry_defaults`: Model catalog initialization and defaults validation.
- `test_02_patch_validation_invalid_values`: Validation rules rejecting out-of-bound judge patches.
- `test_03_persistence_of_judge_changes`: Dynamic runtime updates persist across requests.
- `test_04_test_a_normal_request`: Simple prompt under SLA routes to fastest eligible model (Qwen 2B).
- `test_05_test_b_judge_increases_latency`: Latency increase triggers immediate dynamic switch to next eligible candidate.
- `test_06_test_c_model_disabled`: Disabling active model triggers seamless constraint-preserving failover.
- `test_07_test_d_impossible_constraints`: Impossible constraints return clean `NO_VALID_MODEL` rejection.
- `test_08_test_e_reset_defaults`: Reset restores factory model configuration.
- `test_09` to `test_18`: SLA hard boundary enforcement, neural complexity, load balancing, and vision detection.

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Gateway health status, model counts, and router state |
| `GET` | `/api/models` | List all models with real-time latency, context, and reliability |
| `GET` | `/api/models/{id}` | Retrieve individual model specifications |
| `PATCH` | `/api/models/{id}` | Update model parameters at runtime (Judge controls) |
| `POST` | `/api/models/reset` | Restore all models to default configurations |
| `POST` | `/api/infer` | Dispatch query with constraint validation & dynamic failover |
| `POST` | `/api/route` | Dry-run routing analysis without executing model generation |
| `GET` | `/api/logs` | Fetch comprehensive audit logs with full explainability matrices |
| `GET` | `/api/stats` | Observability metrics (requests, success rate, latency breakdown) |
| `GET` | `/api/brain` | Prompt Analyzer neural accuracy, evaluation sets, and metadata |

---

## 📊 Observability & UI Highlights

- **Dynamic Explainability Box**: Visualizes the decision winner, prompt parameters, and pass/fail reasons for all candidates.
- **Model Inspector & Sliders**: Live runtime adjustments for model latency, capability, and availability.
- **Context Capacity Bar**: Visualizes token window limits against prompt requirements.
- **Detailed Analysis Dashboard**:
  - **Spider Radar Benchmark**: Geometric multi-axis performance profile (Capability, Speed, Context, Cost Efficiency, Reliability).
  - **Engine Allocation Share**: Real-time traffic distribution across models.
  - **Audit Trail**: Request IDs, timestamps, prompt snapshots, response times, and failover traces.
