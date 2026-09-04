from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.domain import Agent, AgentPassport
from app.schemas.domain import AgentPassportSchema, AgentReputationResponse, BlastRadiusResponse
from app.services.reputation import reputation_engine
from app.services.blast_radius import blast_radius_calculator

router = APIRouter(prefix="/agents", tags=["Agents"])

@router.get("/{agent_id}/passport", response_model=AgentPassportSchema)
async def get_agent_passport(agent_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Agent, AgentPassport).join(AgentPassport, Agent.id == AgentPassport.agent_id).where(Agent.id == agent_id))
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Agent or Passport not found")
    agent, passport = row
    return AgentPassportSchema(
        agent_id=agent.id,
        agent_name=agent.name,
        trust_level=agent.trust_level,
        single_tx_limit=passport.single_tx_limit,
        daily_spend_limit=passport.daily_spend_limit,
        max_daily_transactions=passport.max_daily_transactions,
        allowed_categories=passport.allowed_categories or [],
        allowed_merchants=passport.allowed_merchants or [],
        recurring_allowed=passport.recurring_allowed
    )

@router.get("/{agent_id}/reputation", response_model=AgentReputationResponse)
async def get_agent_reputation(agent_id: str):
    data = await reputation_engine.get_reputation(agent_id)
    return AgentReputationResponse(**data)

@router.get("/{agent_id}/blast-radius", response_model=BlastRadiusResponse)
async def get_agent_blast_radius(agent_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AgentPassport).where(AgentPassport.agent_id == agent_id))
    passport = res.scalars().first()
    if not passport:
        raise HTTPException(status_code=404, detail="Agent passport not found")
    data = blast_radius_calculator.calculate_exposure(passport)
    return BlastRadiusResponse(**data)
