const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface IntentExtractResponse {
  intent_id: string;
  user_id: string;
  agent_id: string;
  raw_prompt: string;
  category: string;
  purpose: string;
  max_budget: number;
  currency: string;
  quantity: number;
  authorization_type: string;
  recurring_allowed: boolean;
  fingerprint: string;
  expiry_timestamp: number;
  explicit_constraints: Record<string, any>;
  inferred_assumptions: Record<string, any>;
}

export interface PolicyEvaluationDetail {
  check_name: string;
  status: string; // PASS, FAIL, WARNING
  message: string;
  data: Record<string, any>;
}

export interface TransactionAuthorizeResponse {
  transaction_id: string;
  idempotency_key: string;
  decision: string; // ALLOW, BLOCK
  status: string;
  block_reason?: string;
  price_variance: number;
  intent_fingerprint: string;
  evaluations: PolicyEvaluationDetail[];
  razorpay_order_id?: string;
  razorpay_key_id?: string;
}

export interface TransactionReplayEvent {
  id: string;
  stage: string;
  actor: string;
  decision: string;
  reason: string;
  event_metadata: Record<string, any>;
  timestamp: string;
}

export interface TransactionReplayResponse {
  transaction_id: string;
  idempotency_key: string;
  status: string;
  decision: string;
  final_price: number;
  events: TransactionReplayEvent[];
}

export interface ChaosScenario {
  id: string;
  name: string;
  description: string;
  active: boolean;
}

export interface DashboardOverview {
  total_transactions_evaluated: number;
  allowed_count: number;
  blocked_count: number;
  intent_drift_count: number;
  circuit_breaker_active_count: number;
  total_protected_exposure: number;
  average_agent_trust_score: number;
  recent_transactions: any[];
  recent_events: any[];
}

export async function fetchOverview(): Promise<DashboardOverview> {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard/overview`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Backend error");
    return await res.json();
  } catch (err) {
    return {
      total_transactions_evaluated: 18,
      allowed_count: 14,
      blocked_count: 4,
      intent_drift_count: 3,
      circuit_breaker_active_count: 0,
      total_protected_exposure: 250000.0,
      average_agent_trust_score: 94.0,
      recent_transactions: [],
      recent_events: []
    };
  }
}

export async function extractIntent(prompt: string, agentId: string = "agent_shopping_alpha"): Promise<IntentExtractResponse> {
  const res = await fetch(`${API_BASE_URL}/intents/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_prompt: prompt, agent_id: agentId }),
  });
  if (!res.ok) throw new Error("Failed to extract intent");
  return await res.json();
}

export async function authorizeTransaction(payload: {
  agent_id: string;
  intent_id: string;
  intent_fingerprint: string;
  product_id: string;
  proposed_price: number;
  proposed_quantity?: number;
  idempotency_key: string;
}): Promise<TransactionAuthorizeResponse> {
  const res = await fetch(`${API_BASE_URL}/transactions/authorize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Transaction evaluation failed");
  return await res.json();
}

export async function fetchReplay(transactionId: string): Promise<TransactionReplayResponse> {
  const res = await fetch(`${API_BASE_URL}/transactions/${transactionId}/replay`, { cache: 'no-store' });
  if (!res.ok) throw new Error("Replay fetch failed");
  return await res.json();
}

export async function fetchChaosScenarios(): Promise<ChaosScenario[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/chaos`, { cache: 'no-store' });
    if (!res.ok) throw new Error("Chaos fetch failed");
    return await res.json();
  } catch (e) {
    return [];
  }
}

export async function injectChaos(scenarioId: string, active: boolean): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/chaos/inject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scenario_id: scenarioId, active }),
  });
  return await res.json();
}

export async function resetChaos(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/chaos/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });
  return await res.json();
}
