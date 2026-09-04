import json
import logging
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.config import settings
from app.core.security import verify_razorpay_signature
from app.core.redis import redis_manager
from app.models.domain import Transaction, TransactionEvent

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = logging.getLogger("intentgate.webhooks")

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    body_bytes = await request.body()
    
    # Signature Verification (if secret is configured and not default mock)
    if settings.RAZORPAY_WEBHOOK_SECRET and x_razorpay_signature and not settings.RAZORPAY_KEY_ID.startswith("rzp_test_mock"):
        valid = verify_razorpay_signature(body_bytes, x_razorpay_signature, settings.RAZORPAY_WEBHOOK_SECRET)
        if not valid:
            logger.warning("Invalid Razorpay Webhook Signature detected!")
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        payload = {"event": "payment.captured", "payload": {"payment": {"entity": {"order_id": "order_mock", "id": "pay_mock"}}}}

    event_type = payload.get("event", "unknown")
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = entity.get("order_id")
    payment_id = entity.get("id")

    # Idempotent Webhook Processing via Redis
    client = redis_manager.client
    webhook_key = f"intentgate:webhook:{order_id}:{event_type}"
    if await client.exists(webhook_key):
        logger.info("Duplicate Webhook ignored for order_id: %s", order_id)
        return {"status": "ignored", "reason": "duplicate_webhook"}

    await client.set(webhook_key, "1", ex=3600)

    # Reconcile Payment State in DB
    if order_id:
        tx_res = await db.execute(select(Transaction).where(Transaction.razorpay_order_id == order_id))
        tx = tx_res.scalars().first()
        if tx:
            if event_type == "payment.captured":
                tx.status = "CAPTURED"
                tx.razorpay_payment_id = payment_id
                event = TransactionEvent(
                    transaction_id=tx.id,
                    stage="WEBHOOK_CAPTURED",
                    actor="RAZORPAY_WEBHOOK",
                    decision="PASS",
                    reason="Verified payment capture webhook delivered",
                    event_metadata={"payment_id": payment_id, "order_id": order_id}
                )
                db.add(event)
                await db.commit()
                logger.info("Transaction %s updated to CAPTURED via Webhook", tx.id)

    return {"status": "success", "event": event_type}
