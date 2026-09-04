import pytest
import time
import hashlib
import json
import hmac
from datetime import datetime, timedelta
from app.core.security import generate_intent_fingerprint, normalize_intent_dict
from app.services.policy_engine import policy_engine
from app.services.freshness import FreshnessGuardService
from app.models.domain import UserIntent, AgentPassport, MerchantPolicy, Product

@pytest.mark.asyncio
async def test_fingerprint_hmac_salting_and_determinism():
    dict1 = {"category": "laptop", "max_budget": 70000.0, "purpose": "programming", "quantity": 1}
    dict2 = {"purpose": "programming", "quantity": 1, "max_budget": 70000.0, "category": "laptop"}
    secret = "user_demo_secret"
    
    fp1 = generate_intent_fingerprint(dict1, user_secret=secret)
    fp2 = generate_intent_fingerprint(dict2, user_secret=secret)
    assert fp1 == fp2, "HMAC-SHA256 Fingerprint must be key-order invariant"
    
    # Prove HMAC fingerprint differs from unsalted plain SHA-256
    canonical_json = json.dumps(normalize_intent_dict(dict1), sort_keys=True, separators=(',', ':'))
    plain_sha256 = hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
    assert fp1 != plain_sha256, "HMAC fingerprint with secret MUST differ from plain unsalted SHA-256"

@pytest.mark.asyncio
async def test_policy_engine_allow():
    intent = UserIntent(
        max_budget=70000.0,
        quantity=1,
        fingerprint="fp_valid_123",
        expiry_timestamp=time.time() + 3600.0
    )
    passport = AgentPassport(
        agent_id="agent_test",
        single_tx_limit=70000.0,
        allowed_categories=["laptop"]
    )
    merchant = MerchantPolicy(max_autonomous_purchase=70000.0)
    product = Product(category="laptop", updated_at=datetime.utcnow())
    
    passed, reason, evals, variance, is_drift = await policy_engine.evaluate_transaction(
        intent=intent,
        passport=passport,
        merchant_policy=merchant,
        product=product,
        proposed_price=68999.0,
        fingerprint_input="fp_valid_123",
        proposed_quantity=1
    )
    assert passed is True
    assert is_drift is False
    assert variance <= 0

@pytest.mark.asyncio
async def test_intent_drift_price_increase_blocks():
    intent = UserIntent(
        max_budget=70000.0,
        quantity=1,
        fingerprint="fp_valid_123",
        expiry_timestamp=time.time() + 3600.0
    )
    passport = AgentPassport(
        agent_id="agent_test",
        single_tx_limit=80000.0,
        allowed_categories=["laptop"]
    )
    merchant = MerchantPolicy(max_autonomous_purchase=80000.0)
    product = Product(category="laptop", updated_at=datetime.utcnow())
    
    passed, reason, evals, variance, is_drift = await policy_engine.evaluate_transaction(
        intent=intent,
        passport=passport,
        merchant_policy=merchant,
        product=product,
        proposed_price=72999.0,
        fingerprint_input="fp_valid_123",
        proposed_quantity=1
    )
    assert passed is False
    assert is_drift is True
    assert variance == 2999.0
    assert "exceeds user budget" in reason

@pytest.mark.asyncio
async def test_quantity_drift_exceeded_blocks():
    intent = UserIntent(
        max_budget=70000.0,
        quantity=1,
        fingerprint="fp_valid_123",
        expiry_timestamp=time.time() + 3600.0
    )
    passport = AgentPassport(
        agent_id="agent_test",
        single_tx_limit=80000.0,
        allowed_categories=["laptop"]
    )
    merchant = MerchantPolicy(max_autonomous_purchase=80000.0)
    product = Product(category="laptop", updated_at=datetime.utcnow())
    
    passed, reason, evals, variance, is_drift = await policy_engine.evaluate_transaction(
        intent=intent,
        passport=passport,
        merchant_policy=merchant,
        product=product,
        proposed_price=68999.0,
        fingerprint_input="fp_valid_123",
        proposed_quantity=3  # Proposed 3 > intent limit 1
    )
    assert passed is False
    assert is_drift is True
    assert "Proposed quantity (3) exceeds user authorized quantity limit (1)" in reason
    qty_eval = next((e for e in evals if e.check_name == "QuantityDriftCheck"), None)
    assert qty_eval is not None
    assert qty_eval.status == "FAIL"

@pytest.mark.asyncio
async def test_data_freshness_guard():
    fresh_time = datetime.utcnow()
    stale_time = datetime.utcnow() - timedelta(seconds=150)
    assert FreshnessGuardService.is_fresh(fresh_time) is True
    assert FreshnessGuardService.is_fresh(stale_time) is False
