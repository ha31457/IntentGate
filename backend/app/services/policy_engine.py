import time
import logging
from typing import List, Tuple, Dict, Any
from app.models.domain import UserIntent, AgentPassport, MerchantPolicy, Product
from app.schemas.domain import PolicyEvaluationDetail
from app.services.circuit_breaker import circuit_breaker_service
from app.services.freshness import FreshnessGuardService

logger = logging.getLogger("intentgate.policy_engine")

class PolicyEngine:
    """Deterministic, non-probabilistic policy evaluation engine."""

    async def evaluate_transaction(
        self,
        intent: UserIntent,
        passport: AgentPassport,
        merchant_policy: MerchantPolicy,
        product: Product,
        proposed_price: float,
        fingerprint_input: str,
        proposed_quantity: int = 1
    ) -> Tuple[bool, str, List[PolicyEvaluationDetail], float, bool]:
        """
        Evaluates all hard policy boundaries.
        Returns: (passed, primary_block_reason, evaluations_list, price_variance, is_drift)
        """
        evaluations: List[PolicyEvaluationDetail] = []
        is_blocked = False
        primary_reason = ""
        is_drift = False
        price_variance = proposed_price - intent.max_budget

        # 1. Circuit Breaker Check
        cb_state = await circuit_breaker_service.get_state(passport.agent_id)
        if cb_state == "OPEN":
            is_blocked = True
            primary_reason = "Circuit Breaker is OPEN due to prior abnormal agent behavior"
            evaluations.append(PolicyEvaluationDetail(
                check_name="CircuitBreakerCheck",
                status="FAIL",
                message=primary_reason,
                data={"circuit_state": cb_state}
            ))
            return False, primary_reason, evaluations, price_variance, False
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="CircuitBreakerCheck",
                status="PASS",
                message="Circuit breaker is CLOSED (Normal Operational State)",
                data={"circuit_state": cb_state}
            ))

        # 2. Intent Fingerprint Integrity & Expiry
        if fingerprint_input != intent.fingerprint:
            is_blocked = True
            primary_reason = "Cryptographic Intent Fingerprint mismatch! Tampering detected."
            evaluations.append(PolicyEvaluationDetail(
                check_name="IntentFingerprintIntegrity",
                status="FAIL",
                message=primary_reason,
                data={"expected": intent.fingerprint, "received": fingerprint_input}
            ))
        elif time.time() > intent.expiry_timestamp:
            is_blocked = True
            primary_reason = "User Intent authorization has expired."
            evaluations.append(PolicyEvaluationDetail(
                check_name="IntentFingerprintIntegrity",
                status="FAIL",
                message=primary_reason,
                data={"expiry": intent.expiry_timestamp, "current_time": time.time()}
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="IntentFingerprintIntegrity",
                status="PASS",
                message="HMAC SHA-256 Intent Fingerprint verified & unexpired",
                data={"fingerprint": intent.fingerprint[:16] + "..."}
            ))

        # 3. Intent Drift Check (Budget Boundary)
        if proposed_price > intent.max_budget:
            is_blocked = True
            is_drift = True
            variance_str = f"+₹{price_variance:,.2f}"
            drift_msg = f"Intent Drift Detected! Proposed price (₹{proposed_price:,.2f}) exceeds user budget limit (₹{intent.max_budget:,.2f}) by {variance_str}."
            if not primary_reason:
                primary_reason = drift_msg
            evaluations.append(PolicyEvaluationDetail(
                check_name="IntentDriftBudgetCheck",
                status="FAIL",
                message=drift_msg,
                data={
                    "user_budget": intent.max_budget,
                    "proposed_price": proposed_price,
                    "variance": price_variance
                }
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="IntentDriftBudgetCheck",
                status="PASS",
                message=f"Price ₹{proposed_price:,.2f} is within budget constraint ≤ ₹{intent.max_budget:,.2f}",
                data={"user_budget": intent.max_budget, "proposed_price": proposed_price}
            ))

        # 3b. Quantity Drift Check
        if proposed_quantity > intent.max_quantity:
            is_blocked = True
            is_drift = True
            qty_drift_msg = f"Intent Drift Detected! Proposed quantity ({proposed_quantity}) exceeds user authorized quantity limit ({intent.max_quantity})."
            if not primary_reason:
                primary_reason = qty_drift_msg
            evaluations.append(PolicyEvaluationDetail(
                check_name="QuantityDriftCheck",
                status="FAIL",
                message=qty_drift_msg,
                data={
                    "user_max_quantity": intent.max_quantity,
                    "proposed_quantity": proposed_quantity
                }
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="QuantityDriftCheck",
                status="PASS",
                message=f"Quantity {proposed_quantity} is within authorized quantity limit ≤ {intent.max_quantity}",
                data={"user_max_quantity": intent.max_quantity, "proposed_quantity": proposed_quantity}
            ))

        # 4. Agent Passport Limits
        if proposed_price > passport.single_tx_limit:
            is_blocked = True
            limit_msg = f"Agent single transaction limit exceeded (Limit: ₹{passport.single_tx_limit:,.2f}, Attempted: ₹{proposed_price:,.2f})."
            if not primary_reason:
                primary_reason = limit_msg
            evaluations.append(PolicyEvaluationDetail(
                check_name="AgentPassportLimitCheck",
                status="FAIL",
                message=limit_msg,
                data={"single_tx_limit": passport.single_tx_limit, "proposed_price": proposed_price}
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="AgentPassportLimitCheck",
                status="PASS",
                message=f"Transaction size ₹{proposed_price:,.2f} complies with Agent Passport limit ≤ ₹{passport.single_tx_limit:,.2f}",
                data={"single_tx_limit": passport.single_tx_limit}
            ))

        # 5. Agent Category Permissions
        if passport.allowed_categories and product.category not in passport.allowed_categories:
            is_blocked = True
            is_drift = True
            cat_msg = f"Agent is unauthorized to purchase category '{product.category}'."
            if not primary_reason:
                primary_reason = cat_msg
            evaluations.append(PolicyEvaluationDetail(
                check_name="AgentCategoryPermissionCheck",
                status="FAIL",
                message=cat_msg,
                data={"product_category": product.category, "allowed": passport.allowed_categories}
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="AgentCategoryPermissionCheck",
                status="PASS",
                message=f"Product category '{product.category}' is permitted by Agent Passport",
                data={"product_category": product.category}
            ))

        # 5b. Product Stock Availability Check
        if product.stock is not None and product.stock <= 0:
            is_blocked = True
            stock_msg = f"Product '{product.title}' is out of stock / unavailable (Stock: 0)."
            if not primary_reason:
                primary_reason = stock_msg
            evaluations.append(PolicyEvaluationDetail(
                check_name="ProductAvailabilityCheck",
                status="FAIL",
                message=stock_msg,
                data={"stock": product.stock}
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="ProductAvailabilityCheck",
                status="PASS",
                message=f"Product inventory stock verified (Stock: {product.stock})",
                data={"stock": product.stock}
            ))

        # 6. Merchant Policy Firewall
        if proposed_price > merchant_policy.max_autonomous_purchase:
            is_blocked = True
            merch_msg = f"Merchant autonomous purchase threshold exceeded (Merchant limit: ₹{merchant_policy.max_autonomous_purchase:,.2f}, Proposed: ₹{proposed_price:,.2f})."
            if not primary_reason:
                primary_reason = merch_msg
            evaluations.append(PolicyEvaluationDetail(
                check_name="MerchantPolicyFirewallCheck",
                status="FAIL",
                message=merch_msg,
                data={"merchant_limit": merchant_policy.max_autonomous_purchase, "proposed_price": proposed_price}
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="MerchantPolicyFirewallCheck",
                status="PASS",
                message=f"Merchant autonomous limit check passed (≤ ₹{merchant_policy.max_autonomous_purchase:,.2f})",
                data={"merchant_limit": merchant_policy.max_autonomous_purchase}
            ))

        # 7. Data Freshness Check
        if not FreshnessGuardService.is_fresh(product.updated_at):
            is_blocked = True
            age = FreshnessGuardService.get_data_age_seconds(product.updated_at)
            fresh_msg = f"Stale financial data rejected! Data age is {age:.1f}s (Max allowed: 120s)."
            if not primary_reason:
                primary_reason = fresh_msg
            evaluations.append(PolicyEvaluationDetail(
                check_name="DataFreshnessCheck",
                status="FAIL",
                message=fresh_msg,
                data={"data_age_seconds": age}
            ))
        else:
            evaluations.append(PolicyEvaluationDetail(
                check_name="DataFreshnessCheck",
                status="PASS",
                message="Financial price data freshness verified",
                data={"data_age_seconds": FreshnessGuardService.get_data_age_seconds(product.updated_at)}
            ))

        return (not is_blocked), primary_reason, evaluations, price_variance, is_drift

policy_engine = PolicyEngine()
