from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class UserIntentExtractRequest(BaseModel):
    user_prompt: str = Field(..., example="Find me a good laptop for programming under ₹70,000. Buy it if you find one that meets my requirements.")
    agent_id: Optional[str] = None

class UserIntentExtractResponse(BaseModel):
    intent_id: str
    user_id: str
    agent_id: str
    raw_prompt: str
    category: str
    purpose: str
    max_budget: float
    currency: str
    quantity: int
    authorization_type: str
    recurring_allowed: bool
    fingerprint: str
    expiry_timestamp: float
    explicit_constraints: Dict[str, Any]
    inferred_assumptions: Dict[str, Any]

class AgentPassportSchema(BaseModel):
    agent_id: str
    agent_name: str
    trust_level: int
    single_tx_limit: float
    daily_spend_limit: float
    max_daily_transactions: int
    allowed_categories: List[str]
    allowed_merchants: List[str]
    recurring_allowed: bool

class TransactionAuthorizeRequest(BaseModel):
    agent_id: str
    intent_id: str
    intent_fingerprint: str
    product_id: str
    proposed_price: float
    proposed_quantity: int = 1
    idempotency_key: str

class PolicyEvaluationDetail(BaseModel):
    check_name: str
    status: str  # PASS, FAIL, WARNING
    message: str
    data: Dict[str, Any] = {}

class TransactionAuthorizeResponse(BaseModel):
    transaction_id: str
    idempotency_key: str
    decision: str  # ALLOW, BLOCK
    status: str
    block_reason: Optional[str] = None
    price_variance: float = 0.0
    intent_fingerprint: str
    evaluations: List[PolicyEvaluationDetail]
    razorpay_order_id: Optional[str] = None
    razorpay_key_id: Optional[str] = None

class TransactionReplayEvent(BaseModel):
    id: str
    stage: str
    actor: str
    decision: str
    reason: str
    event_metadata: Dict[str, Any]
    timestamp: str

class TransactionReplayResponse(BaseModel):
    transaction_id: str
    idempotency_key: str
    status: str
    decision: str
    final_price: float
    events: List[TransactionReplayEvent]

class ChaosInjectRequest(BaseModel):
    scenario_id: str  # e.g., PRICE_CHANGED, STALE_DATA, PAYMENT_TIMEOUT, etc.
    active: bool = True
    payload: Dict[str, Any] = {}

class ChaosScenarioStatus(BaseModel):
    id: str
    name: str
    active: bool
    payload: Dict[str, Any]

class AgentReputationResponse(BaseModel):
    agent_id: str
    trust_score: int
    intent_adherence: int
    policy_compliance: int
    transaction_reliability: int
    retry_behavior: int
    total_evaluations: int
    drift_count: int
    blocked_count: int

class BlastRadiusResponse(BaseModel):
    agent_id: str
    unmitigated_daily_exposure: float
    intentgate_protected_max_exposure: float
    single_transaction_limit: float
    max_daily_transactions: int
    recurring_allowed: bool
    protection_percentage: float

class DashboardOverviewResponse(BaseModel):
    total_transactions_evaluated: int
    allowed_count: int
    blocked_count: int
    intent_drift_count: int
    circuit_breaker_active_count: int
    total_protected_exposure: float
    average_agent_trust_score: float
    recent_transactions: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]
