import re
import json
import logging
import time
from typing import Dict, Any, Tuple
from app.core.config import settings

logger = logging.getLogger("intentgate.ai_extractor")

class AIIntentExtractor:
    """Extracts structured intent and assumption ledger from natural language prompt."""
    
    async def extract_intent(self, user_prompt: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        Returns: (intent_dict, explicit_constraints, inferred_assumptions)
        """
        # Try Gemini API if available
        if settings.GEMINI_API_KEY:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.GEMINI_API_KEY)
                model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-3.5-flash')
                model = genai.GenerativeModel(model_name)
                prompt = f"""
Extract structured financial intent from this user shopping request:
"{user_prompt}"

Return ONLY valid JSON matching this structure:
{{
  "category": "laptop",
  "purpose": "programming",
  "max_budget": 70000.0,
  "currency": "INR",
  "quantity": 1,
  "authorization_type": "purchase_if_requirements_met",
  "recurring_allowed": false,
  "explicit_constraints": {{"max_budget": 70000.0, "category": "laptop", "purpose": "programming"}},
  "inferred_assumptions": {{"preferred_ram_gb": 16, "preferred_ssd_gb": 512, "os": "Windows"}}
}}
"""
                response = await model.generate_content_async(prompt)
                content = response.text.strip()
                # Clean code blocks if present
                if content.startswith("```json"):
                    content = content[7:]
                if content.endswith("```"):
                    content = content[:-3]
                parsed = json.loads(content.strip())
                
                intent = {
                    "category": parsed.get("category", "laptop"),
                    "purpose": parsed.get("purpose", "general"),
                    "max_budget": float(parsed.get("max_budget", 70000.0)),
                    "currency": parsed.get("currency", "INR"),
                    "quantity": int(parsed.get("quantity", 1)),
                    "authorization_type": parsed.get("authorization_type", "purchase_if_requirements_met"),
                    "recurring_allowed": bool(parsed.get("recurring_allowed", False)),
                }
                explicit = parsed.get("explicit_constraints", {"max_budget": intent["max_budget"], "category": intent["category"]})
                inferred = parsed.get("inferred_assumptions", {"preferred_ram_gb": 16, "preferred_ssd_gb": 512})
                return intent, explicit, inferred
            except Exception as e:
                logger.warning("Gemini AI extraction failed (%s). Falling back to deterministic extractor.", str(e))

        # Deterministic Regex Fallback (Fast, reliable, offline-capable)
        budget = 70000.0
        # Parse currency numbers like 70,000 or 70000 or Rs 70000
        budget_match = re.search(r'(?:₹|rs\.?|inr)?\s*([\d,]+)', user_prompt, re.IGNORECASE)
        if budget_match:
            try:
                val_str = budget_match.group(1).replace(',', '')
                val = float(val_str)
                if val > 100:  # Avoid matching quantity or small numbers
                    budget = val
            except ValueError:
                pass
        
        category = "laptop"
        if "laptop" in user_prompt.lower() or "computer" in user_prompt.lower() or "macbook" in user_prompt.lower():
            category = "laptop"
        elif "phone" in user_prompt.lower() or "mobile" in user_prompt.lower():
            category = "smartphone"
        elif "console" in user_prompt.lower() or "playstation" in user_prompt.lower() or "xbox" in user_prompt.lower():
            category = "gaming_console"

        purpose = "programming"
        if "program" in user_prompt.lower() or "code" in user_prompt.lower() or "dev" in user_prompt.lower():
            purpose = "programming"
        elif "game" in user_prompt.lower() or "gaming" in user_prompt.lower():
            purpose = "gaming"
            
        intent = {
            "category": category,
            "purpose": purpose,
            "max_budget": budget,
            "currency": "INR",
            "quantity": 1,
            "authorization_type": "purchase_if_requirements_met",
            "recurring_allowed": False
        }
        
        explicit = {
            "max_budget": budget,
            "category": category,
            "purpose": purpose,
            "quantity": 1
        }
        
        inferred = {
            "preferred_ram_gb": 16,
            "preferred_ssd_gb": 512,
            "preferred_os": "Windows / macOS",
            "note": "AI inferred specifications based on programming workload"
        }
        
        return intent, explicit, inferred

ai_extractor_service = AIIntentExtractor()
