from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.domain import Transaction, TransactionEvent, AgentReputation, CircuitBreakerRecord
from app.schemas.domain import DashboardOverviewResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(db: AsyncSession = Depends(get_db)):
    # Total evaluations
    tx_count_res = await db.execute(select(func.count(Transaction.id)))
    total_tx = tx_count_res.scalar() or 0

    # Allowed count
    allowed_res = await db.execute(select(func.count(Transaction.id)).where(Transaction.decision == "ALLOW"))
    allowed_count = allowed_res.scalar() or 0

    # Blocked count
    blocked_res = await db.execute(select(func.count(Transaction.id)).where(Transaction.decision == "BLOCK"))
    blocked_count = blocked_res.scalar() or 0

    # Intent Drift count
    drift_res = await db.execute(select(func.count(Transaction.id)).where(Transaction.block_reason.like("%Intent Drift%")))
    drift_count = drift_res.scalar() or 0

    # Active circuit breakers
    cb_res = await db.execute(select(func.count(CircuitBreakerRecord.id)).where(CircuitBreakerRecord.state == "OPEN"))
    cb_active = cb_res.scalar() or 0

    # Average Trust Score
    rep_res = await db.execute(select(func.avg(AgentReputation.trust_score)))
    avg_trust = float(rep_res.scalar() or 92.0)

    # Recent Transactions
    tx_recent_res = await db.execute(select(Transaction).order_by(Transaction.created_at.desc()).limit(10))
    tx_list = tx_recent_res.scalars().all()
    recent_transactions = [
        {
            "id": tx.id,
            "product_title": tx.product_title,
            "proposed_price": tx.proposed_price,
            "decision": tx.decision,
            "status": tx.status,
            "block_reason": tx.block_reason,
            "created_at": tx.created_at.isoformat()
        }
        for tx in tx_list
    ]

    # Recent Security Events
    events_res = await db.execute(select(TransactionEvent).order_by(TransactionEvent.timestamp.desc()).limit(10))
    events_list = events_res.scalars().all()
    recent_events = [
        {
            "id": ev.id,
            "stage": ev.stage,
            "actor": ev.actor,
            "decision": ev.decision,
            "reason": ev.reason,
            "timestamp": ev.timestamp.isoformat()
        }
        for ev in events_list
    ]

    return DashboardOverviewResponse(
        total_transactions_evaluated=total_tx,
        allowed_count=allowed_count,
        blocked_count=blocked_count,
        intent_drift_count=drift_count,
        circuit_breaker_active_count=cb_active,
        total_protected_exposure=250000.0,
        average_agent_trust_score=round(avg_trust, 1),
        recent_transactions=recent_transactions,
        recent_events=recent_events
    )
