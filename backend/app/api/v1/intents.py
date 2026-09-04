import time
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.domain import UserIntentExtractRequest, UserIntentExtractResponse
from app.services.ai_extractor import ai_extractor_service
from app.core.security import generate_intent_fingerprint
from app.models.domain import UserIntent, IntentAssumption, Agent, AgentPassport
from app.core.config import settings

router = APIRouter(prefix="/intents", tags=["Intents"])
logger = logging.getLogger("intentgate.api.intents")

@router.post("/extract", response_model=UserIntentExtractResponse)
async def extract_intent(
    req: UserIntentExtractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Converts natural language user prompt into structured Intent, Assumption Ledger, and SHA-256 Fingerprint.
    """
    agent_id = req.agent_id or "agent_shopping_alpha"
    
    # Extract structured intent and assumptions
    intent_dict, explicit_constraints, inferred_assumptions = await ai_extractor_service.extract_intent(req.user_prompt)
    
    # Generate Cryptographic HMAC Fingerprint
    user_secret = "user_demo_1"
    fingerprint = generate_intent_fingerprint(intent_dict, user_secret=user_secret)
    expiry_ts = time.time() + settings.DEFAULT_INTENT_EXPIRY_SECONDS
    
    # Store in Database
    user_intent = UserIntent(
        user_id="user_demo_1",
        agent_id=agent_id,
        raw_prompt=req.user_prompt,
        category=intent_dict["category"],
        purpose=intent_dict["purpose"],
        max_budget=intent_dict["max_budget"],
        currency=intent_dict["currency"],
        quantity=intent_dict["quantity"],
        authorization_type=intent_dict["authorization_type"],
        recurring_allowed=intent_dict["recurring_allowed"],
        fingerprint=fingerprint,
        expiry_timestamp=expiry_ts
    )
    db.add(user_intent)
    await db.flush()

    assumption = IntentAssumption(
        intent_id=user_intent.id,
        explicit_constraints=explicit_constraints,
        inferred_assumptions=inferred_assumptions
    )
    db.add(assumption)
    await db.commit()

    return UserIntentExtractResponse(
        intent_id=user_intent.id,
        user_id=user_intent.user_id,
        agent_id=agent_id,
        raw_prompt=req.user_prompt,
        category=user_intent.category,
        purpose=user_intent.purpose,
        max_budget=user_intent.max_budget,
        currency=user_intent.currency,
        quantity=user_intent.quantity,
        authorization_type=user_intent.authorization_type,
        recurring_allowed=user_intent.recurring_allowed,
        fingerprint=fingerprint,
        expiry_timestamp=expiry_ts,
        explicit_constraints=explicit_constraints,
        inferred_assumptions=inferred_assumptions
    )
