import logging
from typing import Dict, Any, List
from app.core.redis import redis_manager

logger = logging.getLogger("intentgate.chaos")

SCENARIOS = {
    "PRICE_CHANGED": {
        "id": "PRICE_CHANGED",
        "name": "Price Changed (Budget Exceeded)",
        "description": "Inflates proposed product price to ₹72,999, violating user's ₹70,000 budget boundary."
    },
    "PRODUCT_UNAVAILABLE": {
        "id": "PRODUCT_UNAVAILABLE",
        "name": "Product Unavailable",
        "description": "Sets product inventory stock to 0."
    },
    "STALE_DATA": {
        "id": "STALE_DATA",
        "name": "Stale Financial Data",
        "description": "Forces product price timestamp age to > 10 minutes, failing data freshness guard."
    },
    "PAYMENT_TIMEOUT": {
        "id": "PAYMENT_TIMEOUT",
        "name": "Payment Gateway Timeout",
        "description": "Simulates API timeout resulting in UNKNOWN payment state. Verifies safe reconciliation."
    },
    "DUPLICATE_REQUEST": {
        "id": "DUPLICATE_REQUEST",
        "name": "Duplicate Transaction Request",
        "description": "Fires twin requests with identical idempotency key to test Redis lock protection."
    },
    "DUPLICATE_WEBHOOK": {
        "id": "DUPLICATE_WEBHOOK",
        "name": "Duplicate Razorpay Webhook",
        "description": "Delivers duplicate Razorpay payment event webhooks to test idempotent webhook handling."
    },
    "DELAYED_WEBHOOK": {
        "id": "DELAYED_WEBHOOK",
        "name": "Delayed Payment Webhook",
        "description": "Simulates out-of-order delayed payment webhook notifications."
    },
    "INTENT_DRIFT": {
        "id": "INTENT_DRIFT",
        "name": "Intent Category Drift",
        "description": "Agent substitutes requested 'laptop' with unauthorized 'gaming_console'."
    },
    "RETRY_STORM": {
        "id": "RETRY_STORM",
        "name": "Agent Retry Storm",
        "description": "Fires 10 rapid transaction requests in 5 seconds to trip the Circuit Breaker."
    },
    "MERCHANT_POLICY_CHANGE": {
        "id": "MERCHANT_POLICY_CHANGE",
        "name": "Merchant Policy Change",
        "description": "Lowers merchant autonomous limit to ₹50,000, triggering merchant policy block."
    },
    "AUTHORIZATION_EXPIRY": {
        "id": "AUTHORIZATION_EXPIRY",
        "name": "Authorization Expiry",
        "description": "Sets user intent timestamp to expired state."
    }
}

class ChaosInjectorService:
    """Manages Chaos / Failure Lab injections stored in Redis."""

    async def set_scenario(self, scenario_id: str, active: bool = True, payload: Dict[str, Any] = {}, clear_others: bool = True) -> Dict[str, Any]:
        client = redis_manager.client
        if active and clear_others:
            await self.reset_all()
        
        key = f"intentgate:chaos:{scenario_id}"
        if active:
            data = {"active": True, "payload": payload}
            await client.set(key, json.dumps(data), ex=3600)
            logger.info("Chaos scenario %s ACTIVATED", scenario_id)
        else:
            await client.delete(key)
            logger.info("Chaos scenario %s DEACTIVATED", scenario_id)
        return {"scenario_id": scenario_id, "active": active}

    async def is_active(self, scenario_id: str) -> bool:
        client = redis_manager.client
        key = f"intentgate:chaos:{scenario_id}"
        val = await client.get(key)
        if not val:
            return False
        try:
            data = json.loads(val)
            return data.get("active", False)
        except Exception:
            return False

    async def reset_all(self):
        client = redis_manager.client
        for s_id in SCENARIOS.keys():
            await client.delete(f"intentgate:chaos:{s_id}")
        logger.info("All chaos scenarios reset to deactivated")

    async def get_all_scenarios(self) -> List[Dict[str, Any]]:
        client = redis_manager.client
        res = []
        for s_id, meta in SCENARIOS.items():
            active = await self.is_active(s_id)
            res.append({
                "id": s_id,
                "name": meta["name"],
                "description": meta["description"],
                "active": active
            })
        return res

chaos_service = ChaosInjectorService()
import json
