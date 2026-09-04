import asyncio
import time
import logging
from datetime import datetime, timedelta
from app.db.session import init_db, AsyncSessionLocal
from app.models.domain import (
    Agent, AgentPassport, MerchantPolicy, Product, UserIntent, IntentAssumption,
    Transaction, TransactionEvent, AgentReputation, CircuitBreakerRecord
)
from app.core.security import generate_intent_fingerprint

logger = logging.getLogger("intentgate.seed")

async def seed_data():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Check existing data
        from sqlalchemy import select
        res = await db.execute(select(Agent))
        if res.scalars().first():
            logger.info("Seed data already exists. Skipping.")
            return

        logger.info("Seeding IntentGate initial demo dataset...")

        # 1. Create Agents
        agent_alpha = Agent(
            id="agent_shopping_alpha",
            name="Shopping Agent Alpha",
            trust_level=3,
            status="ACTIVE"
        )
        agent_beta = Agent(
            id="agent_bargain_beta",
            name="Bargain Hunter Beta",
            trust_level=2,
            status="ACTIVE"
        )
        db.add_all([agent_alpha, agent_beta])
        await db.flush()

        # 2. Agent Passports
        passport_alpha = AgentPassport(
            agent_id=agent_alpha.id,
            single_tx_limit=70000.0,
            daily_spend_limit=100000.0,
            max_daily_transactions=5,
            allowed_categories=["laptop", "programming_laptop", "accessories"],
            allowed_merchants=["TechWorld", "DevStore"],
            recurring_allowed=False
        )
        passport_beta = AgentPassport(
            agent_id=agent_beta.id,
            single_tx_limit=40000.0,
            daily_spend_limit=50000.0,
            max_daily_transactions=3,
            allowed_categories=["laptop", "accessories"],
            allowed_merchants=["TechWorld"],
            recurring_allowed=False
        )
        db.add_all([passport_alpha, passport_beta])

        # 3. Merchant Policies
        merchant_techworld = MerchantPolicy(
            merchant_id="merchant_techworld",
            merchant_name="TechWorld",
            max_autonomous_purchase=70000.0,
            allowed_categories=["laptop", "accessories"],
            recurring_allowed=False
        )
        db.add(merchant_techworld)

        # 4. Products
        p1 = Product(
            id="prod_devbook_pro",
            merchant_id="merchant_techworld",
            merchant_name="TechWorld",
            title="DevBook Pro 15",
            category="laptop",
            price=68999.0,
            currency="INR",
            stock=12,
            ram_gb=16,
            ssd_gb=512,
            updated_at=datetime.utcnow()
        )
        p2 = Product(
            id="prod_codemax_14",
            merchant_id="merchant_techworld",
            merchant_name="TechWorld",
            title="CodeMax 14",
            category="laptop",
            price=64999.0,
            currency="INR",
            stock=8,
            ram_gb=16,
            ssd_gb=512,
            updated_at=datetime.utcnow()
        )
        p3 = Product(
            id="prod_ultradev_x",
            merchant_id="merchant_techworld",
            merchant_name="TechWorld",
            title="UltraDev X 16",
            category="laptop",
            price=74999.0,
            currency="INR",
            stock=5,
            ram_gb=32,
            ssd_gb=1024,
            updated_at=datetime.utcnow()
        )
        db.add_all([p1, p2, p3])

        # 5. User Intent & Fingerprint
        raw_prompt = "Find me a good laptop for programming under ₹70,000. Buy it if you find one that meets my requirements."
        intent_dict = {
            "category": "laptop",
            "purpose": "programming",
            "max_budget": 70000.0,
            "currency": "INR",
            "quantity": 1,
            "authorization_type": "purchase_if_requirements_met",
            "recurring_allowed": False
        }
        fp = generate_intent_fingerprint(intent_dict, user_secret="user_demo_1")
        
        user_intent = UserIntent(
            id="intent_demo_70k",
            user_id="user_demo_1",
            agent_id=agent_alpha.id,
            raw_prompt=raw_prompt,
            category="laptop",
            purpose="programming",
            max_budget=70000.0,
            currency="INR",
            quantity=1,
            authorization_type="purchase_if_requirements_met",
            recurring_allowed=False,
            fingerprint=fp,
            expiry_timestamp=time.time() + 3600.0
        )
        db.add(user_intent)
        await db.flush()

        assumption = IntentAssumption(
            intent_id=user_intent.id,
            explicit_constraints={
                "max_budget": 70000.0,
                "category": "laptop",
                "purpose": "programming",
                "quantity": 1
            },
            inferred_assumptions={
                "preferred_ram_gb": 16,
                "preferred_ssd_gb": 512,
                "preferred_os": "Windows / Linux / macOS",
                "note": "AI inferred 16GB RAM recommendation for development tools"
            }
        )
        db.add(assumption)

        # 6. Baseline Transactions & Events
        tx1 = Transaction(
            id="tx_seed_001",
            idempotency_key="idemp_seed_001",
            agent_id=agent_alpha.id,
            intent_id=user_intent.id,
            intent_fingerprint=fp,
            merchant_id="merchant_techworld",
            product_id=p1.id,
            product_title=p1.title,
            proposed_price=68999.0,
            final_price=68999.0,
            price_variance=0.0,
            decision="ALLOW",
            status="CAPTURED",
            razorpay_order_id="order_rzp_demo_001",
            razorpay_payment_id="pay_rzp_demo_001",
            created_at=datetime.utcnow() - timedelta(minutes=15)
        )
        db.add(tx1)
        await db.flush()

        events1 = [
            TransactionEvent(transaction_id=tx1.id, stage="USER_INTENT_CREATED", actor="USER", decision="PASS", reason="Natural language intent registered", event_metadata={"prompt": raw_prompt}),
            TransactionEvent(transaction_id=tx1.id, stage="INTENT_NORMALIZED", actor="SYSTEM", decision="PASS", reason="Intent normalized deterministically", event_metadata=intent_dict),
            TransactionEvent(transaction_id=tx1.id, stage="FINGERPRINT_GENERATED", actor="SYSTEM", decision="PASS", reason="Cryptographic SHA-256 fingerprint generated", event_metadata={"fingerprint": fp}),
            TransactionEvent(transaction_id=tx1.id, stage="PRODUCT_SELECTED", actor="AGENT", decision="PASS", reason="Selected DevBook Pro 15 (₹68,999)", event_metadata={"product_id": p1.id, "price": 68999.0}),
            TransactionEvent(transaction_id=tx1.id, stage="POLICY_EVALUATED", actor="POLICY_ENGINE", decision="PASS", reason="All 7 deterministic policy checks passed", event_metadata={"checks_passed": 7}),
            TransactionEvent(transaction_id=tx1.id, stage="INTENT_DRIFT_CHECK", actor="POLICY_ENGINE", decision="PASS", reason="Price ₹68,999 is within ₹70,000 budget boundary", event_metadata={"variance": 0.0}),
            TransactionEvent(transaction_id=tx1.id, stage="AUTHORIZATION_GRANTED", actor="POLICY_ENGINE", decision="PASS", reason="Issued short-lived payment authorization token", event_metadata={}),
            TransactionEvent(transaction_id=tx1.id, stage="PAYMENT_CAPTURED", actor="RAZORPAY_SERVICE", decision="PASS", reason="Razorpay test payment captured successfully", event_metadata={"payment_id": "pay_rzp_demo_001"}),
        ]
        db.add_all(events1)

        # 7. Agent Reputation & Circuit Breaker Records
        rep_alpha = AgentReputation(
            agent_id=agent_alpha.id,
            trust_score=94,
            intent_adherence=98,
            policy_compliance=95,
            transaction_reliability=90,
            retry_behavior=92,
            total_evaluations=14,
            drift_count=1,
            blocked_count=1
        )
        rep_beta = AgentReputation(
            agent_id=agent_beta.id,
            trust_score=78,
            intent_adherence=82,
            policy_compliance=75,
            transaction_reliability=70,
            retry_behavior=75,
            total_evaluations=8,
            drift_count=2,
            blocked_count=3
        )
        db.add_all([rep_alpha, rep_beta])

        cb_alpha = CircuitBreakerRecord(agent_id=agent_alpha.id, state="CLOSED", failure_count=0)
        cb_beta = CircuitBreakerRecord(agent_id=agent_beta.id, state="CLOSED", failure_count=0)
        db.add_all([cb_alpha, cb_beta])

        await db.commit()
        logger.info("Database seeding completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
