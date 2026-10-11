// ── All TypeScript interfaces for ModelRouter ────────────────

export interface ModelInfo {
  model_key: string;
  id?: string;
  name: string;
  role: string;
  avg_latency_ms: number;
  max_latency_ms: number;
  measured_latency_ms: number;
  capability_score: number;
  context_length: number;
  reliability: number;
  availability: boolean;
  enabled: boolean;
  cost_per_1k_tokens: number;
  provider: string;
  model_id: string;
  description: string;
  available?: boolean;
}

export interface Constraints {
  max_latency_ms: number;
  max_cost_per_token: number;
  min_capability: number;
  min_context_length: number;
  preference: 'lowest_latency' | 'fastest' | 'highest_capability' | 'cheapest' | 'balanced';
}

export interface CandidateResult {
  model_key: string;
  model_id?: string;
  name: string;
  role?: string;
  status: 'selected' | 'passed' | 'rejected';
  rejection_reason?: string | null;
  score?: number | null;
  score_breakdown?: any;
  avg_latency_ms?: number;
  max_latency_ms?: number;
  capability_score?: number;
  cost_per_1k_tokens?: number;
  available?: boolean;
}

export interface ComplexityInfo {
  score: number;
  label: string;
  inferred_min_capability?: number;
  matched_keywords?: string[];
  explanation?: string;
}

export interface Decision {
  request_id?: string;
  status?: string;
  selected: string | null;
  selected_name?: string;
  complexity: ComplexityInfo;
  candidates: CandidateResult[];
  preference_used?: string;
  explanation?: string;
  failover_chain: string[];
  message?: string;
  error?: string;
}

export interface InferResponse {
  success: boolean;
  response?: string;
  model_used?: string;
  model_name?: string;
  decision?: Decision;
  audit_trail?: any[];
  latency_ms?: number;
  execution_mode?: string;
  simulated?: boolean;
  failover_count?: number;
  status?: string;
  message?: string;
  error?: string;
}

export interface AuditEntry {
  log_id?: string;
  id?: number;
  timestamp?: number;
  timestamp_iso?: string;
  request_id?: string;
  model_used?: string;
  model?: string;
  prompt_preview?: string;
  success?: boolean;
  status?: string;
  decision?: any;
  response_time_ms?: number;
  simulated?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'ai' | 'error';
  content: string;
  modelName?: string;
  modelKey?: string;
  executionMode?: string;
  decision?: Decision;
  timestamp: Date;
  latencyMs?: number;
}
