import time
import json
import logging
from typing import Tuple
from app.core.redis import redis_manager
from app.core.config import settings

logger = logging.getLogger("intentgate.circuit_breaker")

class CircuitBreakerService:
    """Manages Redis-backed distributed circuit breaker state machine per agent."""
    
    async def get_state(self, agent_id: str) -> str:
        client = redis_manager.client
        key = f"intentgate:circuit:{agent_id}"
        val = await client.get(key)
        if not val:
            return "CLOSED"
        
        data = json.loads(val)
        state = data.get("state", "CLOSED")
        tripped_at = data.get("tripped_at", 0)
        
        # Check auto-recovery from OPEN to HALF_OPEN
        if state == "OPEN":
            if time.time() - tripped_at > settings.CIRCUIT_BREAKER_RECOVERY_TIME_SECONDS:
                data["state"] = "HALF_OPEN"
                await client.set(key, json.dumps(data), ex=300)
                logger.info("Circuit breaker for agent %s auto-transitioned from OPEN to HALF_OPEN", agent_id)
                return "HALF_OPEN"
                
        return state

    async def record_failure(self, agent_id: str, reason: str = "Policy failure") -> Tuple[str, int]:
        client = redis_manager.client
        key = f"intentgate:circuit:{agent_id}"
        val = await client.get(key)
        
        if val:
            data = json.loads(val)
        else:
            data = {"state": "CLOSED", "failure_count": 0, "tripped_at": 0, "last_reason": ""}
            
        data["failure_count"] += 1
        data["last_reason"] = reason
        
        if data["failure_count"] >= settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD:
            data["state"] = "OPEN"
            data["tripped_at"] = time.time()
            logger.warning("Circuit breaker TRIPPED to OPEN for agent %s! Count: %d, Reason: %s", 
                           agent_id, data["failure_count"], reason)
            
        await client.set(key, json.dumps(data), ex=300)
        return data["state"], data["failure_count"]

    async def record_success(self, agent_id: str):
        client = redis_manager.client
        key = f"intentgate:circuit:{agent_id}"
        val = await client.get(key)
        if val:
            data = json.loads(val)
            if data.get("state") == "HALF_OPEN":
                # Reset back to CLOSED
                data = {"state": "CLOSED", "failure_count": 0, "tripped_at": 0, "last_reason": ""}
                await client.set(key, json.dumps(data), ex=300)
                logger.info("Circuit breaker for agent %s recovered to CLOSED following successful tx", agent_id)

    async def reset(self, agent_id: str):
        client = redis_manager.client
        key = f"intentgate:circuit:{agent_id}"
        data = {"state": "CLOSED", "failure_count": 0, "tripped_at": 0, "last_reason": "Manual reset"}
        await client.set(key, json.dumps(data), ex=300)
        logger.info("Circuit breaker for agent %s manually reset to CLOSED", agent_id)

circuit_breaker_service = CircuitBreakerService()
