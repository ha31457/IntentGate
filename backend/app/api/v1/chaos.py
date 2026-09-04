from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.schemas.domain import ChaosInjectRequest
from app.services.chaos_injector import chaos_service
from app.services.circuit_breaker import circuit_breaker_service

router = APIRouter(prefix="/chaos", tags=["Chaos Lab"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_chaos_scenarios():
    return await chaos_service.get_all_scenarios()

@router.post("/inject")
async def inject_chaos(req: ChaosInjectRequest):
    res = await chaos_service.set_scenario(req.scenario_id, req.active, req.payload)
    return {"status": "success", "scenario": res}

@router.post("/reset")
async def reset_chaos():
    await chaos_service.reset_all()
    await circuit_breaker_service.reset("agent_shopping_alpha")
    await circuit_breaker_service.reset("agent_bargain_beta")
    return {"status": "success", "message": "All failure injections and circuit breakers reset"}
