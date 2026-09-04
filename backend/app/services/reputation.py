import json
import logging
from typing import Dict, Any
from app.core.redis import redis_manager

logger = logging.getLogger("intentgate.reputation")

class ReputationEngine:
    """Calculates operational trust score and records security metric counters."""

    async def record_evaluation(self, agent_id: str, passed: bool, is_drift: bool):
        client = redis_manager.client
        key = f"intentgate:agent:reputation:{agent_id}"
        
        await client.incrby(f"{key}:total", 1)
        if not passed:
            await client.incrby(f"{key}:blocked", 1)
        if is_drift:
            await client.incrby(f"{key}:drift", 1)

    async def get_reputation(self, agent_id: str) -> Dict[str, Any]:
        client = redis_manager.client
        key = f"intentgate:agent:reputation:{agent_id}"
        
        total_raw = await client.get(f"{key}:total")
        blocked_raw = await client.get(f"{key}:blocked")
        drift_raw = await client.get(f"{key}:drift")
        
        total = int(total_raw) if total_raw else 10
        blocked = int(blocked_raw) if blocked_raw else 1
        drift = int(drift_raw) if drift_raw else 1
        
        passed = max(0, total - blocked)
        
        # Calculate Component Scores
        intent_adherence = max(20, int(100 - ((drift / max(1, total)) * 100)))
        policy_compliance = max(20, int((passed / max(1, total)) * 100))
        transaction_reliability = max(30, int(100 - ((blocked / max(1, total)) * 50)))
        retry_behavior = max(50, 95 - (blocked * 2))
        
        # Weighted overall trust score
        trust_score = int(
            (intent_adherence * 0.35) +
            (policy_compliance * 0.35) +
            (transaction_reliability * 0.15) +
            (retry_behavior * 0.15)
        )
        trust_score = min(100, max(0, trust_score))
        
        return {
            "agent_id": agent_id,
            "trust_score": trust_score,
            "intent_adherence": intent_adherence,
            "policy_compliance": policy_compliance,
            "transaction_reliability": transaction_reliability,
            "retry_behavior": retry_behavior,
            "total_evaluations": total,
            "drift_count": drift,
            "blocked_count": blocked
        }

reputation_engine = ReputationEngine()
