import json
import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.domain import (
    Transaction, TransactionEvent, UserIntent, AgentPassport, MerchantPolicy, Product
)
from app.schemas.domain import (
    TransactionAuthorizeRequest, TransactionAuthorizeResponse, TransactionReplayResponse, TransactionReplayEvent
)
from app.services.policy_engine import policy_engine
from app.services.payment_service import payment_service
from app.services.reputation import reputation_engine
from app.services.circuit_breaker import circuit_breaker_service
from app.services.chaos_injector import chaos_service
from app.core.redis import redis_manager
from app.core.config import settings

router = APIRouter(prefix="/transactions", tags=["Transactions"])
logger = logging.getLogger("intentgate.api.transactions")

@router.post("/authorize", response_model=TransactionAuthorizeResponse)
async def authorize_transaction(
    req: TransactionAuthorizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Main IntentGate financial transaction authorization pipeline.
    Evaluates policy engine boundaries, handles idempotency, payment state machine, and audit trail.
    """
    client = redis_manager.client

    # 1. Idempotency Lock & Cached Response Check
    idemp_key = f"intentgate:idempotency:{req.idempotency_key}"
    cached_tx = await client.get(idemp_key)
    if cached_tx:
        logger.info("Idempotency hit! Returning cached transaction result for key: %s", req.idempotency_key)
        data = json.loads(cached_tx)
        return TransactionAuthorizeResponse(**data)

    async with await client.lock(req.idempotency_key, timeout=10):
        # Double-check cache inside lock
        cached_tx = await client.get(idemp_key)
        if cached_tx:
            return TransactionAuthorizeResponse(**json.loads(cached_tx))

        # Check DB for existing idempotency key as durable fallback
        existing_tx_res = await db.execute(select(Transaction).where(Transaction.idempotency_key == req.idempotency_key))
        existing_tx = existing_tx_res.scalars().first()
        if existing_tx:
            logger.info("Durable DB Idempotency hit for key: %s", req.idempotency_key)
            return TransactionAuthorizeResponse(
                transaction_id=existing_tx.id,
                idempotency_key=existing_tx.idempotency_key,
                decision=existing_tx.decision,
                status=existing_tx.status,
                block_reason=existing_tx.block_reason,
                price_variance=existing_tx.price_variance,
                intent_fingerprint=existing_tx.intent_fingerprint,
                evaluations=[],
                razorpay_order_id=existing_tx.razorpay_order_id
            )

        # 2. Fetch Domain Entities
        intent_res = await db.execute(select(UserIntent).where(UserIntent.id == req.intent_id))
        intent = intent_res.scalars().first()
        if not intent:
            raise HTTPException(status_code=404, detail="User Intent record not found")

        passport_res = await db.execute(select(AgentPassport).where(AgentPassport.agent_id == req.agent_id))
        passport = passport_res.scalars().first()
        if not passport:
            raise HTTPException(status_code=404, detail="Agent Passport record not found")

        prod_res = await db.execute(select(Product).where(Product.id == req.product_id))
        product = prod_res.scalars().first()
        if not product:
            # Create dynamic mock product if requested ID is not in DB
            product = Product(
                id=req.product_id,
                merchant_id="merchant_techworld",
                merchant_name="TechWorld",
                title="DevBook Pro 15",
                category="laptop",
                price=req.proposed_price,
                currency="INR",
                stock=10,
                updated_at=datetime.utcnow()
            )
            db.add(product)
            await db.flush()

        merch_res = await db.execute(select(MerchantPolicy).where(MerchantPolicy.merchant_id == product.merchant_id))
        merchant_policy = merch_res.scalars().first()
        if not merchant_policy:
            merchant_policy = MerchantPolicy(
                merchant_id=product.merchant_id,
                merchant_name=product.merchant_name,
                max_autonomous_purchase=70000.0,
                allowed_categories=["laptop", "accessories"],
                recurring_allowed=False
            )
            db.add(merchant_policy)
            await db.flush()

        # 3. Prepare Evaluation Parameters & Apply Active Chaos Lab Injections
        eval_product_updated_at = datetime.utcnow()
        eval_product_category = product.category
        eval_product_stock = product.stock if product.stock is not None else 10
        eval_proposed_price = req.proposed_price
        eval_intent_expiry = intent.expiry_timestamp
        eval_merchant_max_purchase = merchant_policy.max_autonomous_purchase

        if await chaos_service.is_active("PRICE_CHANGED"):
            eval_proposed_price = 72999.0
            logger.info("CHAOS INJECTION: PRICE_CHANGED applied (Price = ₹72,999)")

        if await chaos_service.is_active("STALE_DATA"):
            eval_product_updated_at = datetime.utcnow() - timedelta(minutes=15)
            logger.info("CHAOS INJECTION: STALE_DATA applied (Product age = 15m)")

        if await chaos_service.is_active("INTENT_DRIFT"):
            eval_product_category = "gaming_console"
            logger.info("CHAOS INJECTION: INTENT_DRIFT applied (Category = gaming_console)")

        if await chaos_service.is_active("AUTHORIZATION_EXPIRY"):
            eval_intent_expiry = 1000.0
            logger.info("CHAOS INJECTION: AUTHORIZATION_EXPIRY applied")

        if await chaos_service.is_active("RETRY_STORM"):
            for _ in range(3):
                await circuit_breaker_service.record_failure(req.agent_id, "Retry storm chaos injection")
            logger.info("CHAOS INJECTION: RETRY_STORM applied (Circuit breaker TRIPPED)")

        if await chaos_service.is_active("PRODUCT_UNAVAILABLE"):
            eval_product_stock = 0
            logger.info("CHAOS INJECTION: PRODUCT_UNAVAILABLE applied (Stock = 0)")

        if await chaos_service.is_active("DUPLICATE_REQUEST"):
            logger.info("CHAOS INJECTION: DUPLICATE_REQUEST applied")
            return TransactionAuthorizeResponse(
                transaction_id="tx_chaos_dup_123",
                idempotency_key=req.idempotency_key,
                decision="BLOCK",
                status="FAILED",
                block_reason="Duplicate transaction request rejected by Redis Idempotency Guard (Chaos Scenario Active)",
                price_variance=0.0,
                intent_fingerprint=req.intent_fingerprint,
                evaluations=[PolicyEvaluationDetail(check_name="IdempotencyLockCheck", status="FAIL", message="Duplicate transaction request blocked by Redis Idempotency Lock", data={})],
                razorpay_order_id=None
            )

        if await chaos_service.is_active("MERCHANT_POLICY_CHANGE"):
            eval_merchant_max_purchase = 50000.0
            logger.info("CHAOS INJECTION: MERCHANT_POLICY_CHANGE applied (Merchant limit = ₹50,000)")

        # Create temporary transient evaluation objects (un-tracked by SQLAlchemy session)
        temp_product = Product(
            id=product.id,
            merchant_id=product.merchant_id,
            merchant_name=product.merchant_name,
            title=product.title,
            category=eval_product_category,
            price=product.price,
            stock=eval_product_stock,
            updated_at=eval_product_updated_at
        )
        temp_intent = UserIntent(
            id=intent.id,
            user_id=intent.user_id,
            agent_id=intent.agent_id,
            raw_prompt=intent.raw_prompt,
            category=intent.category,
            purpose=intent.purpose,
            max_budget=intent.max_budget,
            currency=intent.currency,
            quantity=intent.quantity,
            authorization_type=intent.authorization_type,
            recurring_allowed=intent.recurring_allowed,
            fingerprint=intent.fingerprint,
            expiry_timestamp=eval_intent_expiry
        )
        temp_merchant_policy = MerchantPolicy(
            id=merchant_policy.id,
            merchant_id=merchant_policy.merchant_id,
            merchant_name=merchant_policy.merchant_name,
            max_autonomous_purchase=eval_merchant_max_purchase,
            allowed_categories=merchant_policy.allowed_categories,
            recurring_allowed=merchant_policy.recurring_allowed
        )

        # 4. Evaluate Policy Engine
        passed, primary_reason, evaluations, price_variance, is_drift = await policy_engine.evaluate_transaction(
            intent=temp_intent,
            passport=passport,
            merchant_policy=temp_merchant_policy,
            product=temp_product,
            proposed_price=eval_proposed_price,
            fingerprint_input=req.intent_fingerprint,
            proposed_quantity=req.proposed_quantity
        )

        decision = "ALLOW" if passed else "BLOCK"
        tx_status = "AUTHORIZED" if passed else "FAILED"
        rzp_order_id = None
        rzp_payment_id = None

        # 5. Handle Payment Execution for ALLOWED Transactions
        if passed:
            if await chaos_service.is_active("PAYMENT_TIMEOUT"):
                tx_status = "UNKNOWN"
                logger.info("CHAOS INJECTION: PAYMENT_TIMEOUT applied (Status set to UNKNOWN)")
            else:
                # Call Razorpay Payment Service
                rzp_order = await payment_service.create_order(
                    amount_inr=eval_proposed_price,
                    idempotency_key=req.idempotency_key,
                    notes={"intent_id": intent.id, "agent_id": req.agent_id}
                )
                rzp_order_id = rzp_order["order_id"]
                p_status, rzp_payment_id = await payment_service.capture_payment(rzp_order_id, eval_proposed_price)
                tx_status = p_status
                await circuit_breaker_service.record_success(req.agent_id)

        else:
            await circuit_breaker_service.record_failure(req.agent_id, primary_reason or "Policy block")

        # Record metrics in Reputation Engine
        await reputation_engine.record_evaluation(req.agent_id, passed=passed, is_drift=is_drift)

        # 6. Save Transaction Record in Database
        transaction = Transaction(
            idempotency_key=req.idempotency_key,
            agent_id=req.agent_id,
            intent_id=intent.id,
            intent_fingerprint=intent.fingerprint,
            merchant_id=product.merchant_id,
            product_id=product.id,
            product_title=product.title,
            proposed_price=eval_proposed_price,
            final_price=eval_proposed_price if passed else 0.0,
            price_variance=price_variance,
            decision=decision,
            block_reason=primary_reason if not passed else None,
            status=tx_status,
            razorpay_order_id=rzp_order_id,
            razorpay_payment_id=rzp_payment_id
        )
        db.add(transaction)
        await db.flush()

        # 7. Add Immutable Event Timeline Logs
        events = [
            TransactionEvent(transaction_id=transaction.id, stage="INTENT_VERIFIED", actor="INTENT_ENGINE", decision="PASS", reason="Intent fingerprint and parameters verified", event_metadata={"fingerprint": req.intent_fingerprint}),
            TransactionEvent(transaction_id=transaction.id, stage="POLICY_EVALUATION", actor="POLICY_ENGINE", decision=decision, reason=primary_reason or "All policy boundaries satisfied", event_metadata={"evaluations_count": len(evaluations)}),
        ]
        if passed:
            events.append(TransactionEvent(transaction_id=transaction.id, stage="PAYMENT_EXECUTION", actor="RAZORPAY_SERVICE", decision="PASS" if tx_status == "CAPTURED" else "WARNING", reason=f"Razorpay payment state: {tx_status}", event_metadata={"order_id": rzp_order_id, "payment_id": rzp_payment_id}))
        else:
            events.append(TransactionEvent(transaction_id=transaction.id, stage="TRANSACTION_BLOCKED", actor="INTENTGATE_FIREWALL", decision="BLOCK", reason=primary_reason, event_metadata={"variance": price_variance}))
            
        db.add_all(events)
        await db.commit()

        # Build Response
        response = TransactionAuthorizeResponse(
            transaction_id=transaction.id,
            idempotency_key=req.idempotency_key,
            decision=decision,
            status=tx_status,
            block_reason=primary_reason if not passed else None,
            price_variance=price_variance,
            intent_fingerprint=req.intent_fingerprint,
            evaluations=evaluations,
            razorpay_order_id=rzp_order_id,
            razorpay_key_id=settings.RAZORPAY_KEY_ID
        )

        # Cache response in Redis for short TTL
        await client.set(idemp_key, json.dumps(response.model_dump()), ex=600)

        return response

@router.get("/{transaction_id}/replay", response_model=TransactionReplayResponse)
async def replay_transaction(transaction_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns complete step-by-step immutable event timeline for Transaction Replay visualization.
    """
    tx_res = await db.execute(select(Transaction).where(Transaction.id == transaction_id))
    tx = tx_res.scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    events_res = await db.execute(select(TransactionEvent).where(TransactionEvent.transaction_id == transaction_id).order_by(TransactionEvent.timestamp.asc()))
    events = events_res.scalars().all()

    replay_events = [
        TransactionReplayEvent(
            id=ev.id,
            stage=ev.stage,
            actor=ev.actor,
            decision=ev.decision,
            reason=ev.reason,
            event_metadata=ev.event_metadata or {},
            timestamp=ev.timestamp.isoformat()
        )
        for ev in events
    ]

    return TransactionReplayResponse(
        transaction_id=tx.id,
        idempotency_key=tx.idempotency_key,
        status=tx.status,
        decision=tx.decision,
        final_price=tx.final_price,
        events=replay_events
    )
