import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from app.db.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    trust_level = Column(Integer, default=3)  # Level 1 to 5
    status = Column(String, default="ACTIVE")  # ACTIVE, SUSPENDED, BLOCKED
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentPassport(Base):
    __tablename__ = "agent_passports"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), unique=True, nullable=False)
    single_tx_limit = Column(Float, nullable=False, default=70000.0)
    daily_spend_limit = Column(Float, nullable=False, default=100000.0)
    max_daily_transactions = Column(Integer, nullable=False, default=5)
    allowed_categories = Column(JSON, default=list)  # ["laptop", "accessories"]
    allowed_merchants = Column(JSON, default=list)   # ["TechWorld", "DevStore"]
    recurring_allowed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserIntent(Base):
    __tablename__ = "user_intents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False, default="user_demo_1")
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    raw_prompt = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    purpose = Column(String, nullable=False)
    max_budget = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    quantity = Column(Integer, default=1)
    authorization_type = Column(String, default="purchase_if_requirements_met")
    recurring_allowed = Column(Boolean, default=False)
    fingerprint = Column(String, index=True, nullable=False)
    expiry_timestamp = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def max_quantity(self) -> int:
        return self.quantity or 1

class IntentAssumption(Base):
    __tablename__ = "intent_assumptions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    intent_id = Column(String, ForeignKey("user_intents.id"), nullable=False)
    explicit_constraints = Column(JSON, default=dict)
    inferred_assumptions = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, unique=True, nullable=False)
    merchant_name = Column(String, nullable=False)
    max_autonomous_purchase = Column(Float, nullable=False, default=70000.0)
    allowed_categories = Column(JSON, default=list)
    recurring_allowed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    merchant_id = Column(String, nullable=False, default="merchant_techworld")
    merchant_name = Column(String, default="TechWorld")
    title = Column(String, nullable=False)
    category = Column(String, nullable=False, default="laptop")
    price = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    stock = Column(Integer, default=10)
    ram_gb = Column(Integer, default=16)
    ssd_gb = Column(Integer, default=512)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    intent_id = Column(String, ForeignKey("user_intents.id"), nullable=False)
    intent_fingerprint = Column(String, index=True, nullable=False)
    merchant_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    product_title = Column(String, nullable=False)
    proposed_price = Column(Float, nullable=False)
    final_price = Column(Float, nullable=False)
    price_variance = Column(Float, default=0.0)
    decision = Column(String, nullable=False)  # ALLOW, BLOCK
    block_reason = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="CREATED")  # CREATED, AUTHORIZED, CAPTURED, FAILED, UNKNOWN
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TransactionEvent(Base):
    __tablename__ = "transaction_events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transactions.id"), index=True, nullable=False)
    stage = Column(String, nullable=False)  # e.g., USER_INTENT_CREATED, FINGERPRINT_GENERATED, INTENT_DRIFT_CHECK, etc.
    actor = Column(String, nullable=False)  # USER, AGENT, POLICY_ENGINE, RAZORPAY_SERVICE
    decision = Column(String, nullable=False)  # PASS, FAIL, INFO
    reason = Column(Text, nullable=False)
    event_metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentReputation(Base):
    __tablename__ = "agent_reputations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), unique=True, nullable=False)
    trust_score = Column(Integer, default=100)
    intent_adherence = Column(Integer, default=100)
    policy_compliance = Column(Integer, default=100)
    transaction_reliability = Column(Integer, default=100)
    retry_behavior = Column(Integer, default=100)
    total_evaluations = Column(Integer, default=0)
    drift_count = Column(Integer, default=0)
    blocked_count = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CircuitBreakerRecord(Base):
    __tablename__ = "circuit_breaker_records"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.id"), unique=True, nullable=False)
    state = Column(String, default="CLOSED")  # CLOSED, OPEN, HALF_OPEN
    failure_count = Column(Integer, default=0)
    tripped_at = Column(DateTime, nullable=True)
    last_failure_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ChaosScenarioRecord(Base):
    __tablename__ = "chaos_scenarios"
    
    id = Column(String, primary_key=True)  # e.g. PRICE_CHANGED, STALE_DATA
    name = Column(String, nullable=False)
    active = Column(Boolean, default=False)
    payload = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
