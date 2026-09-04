from typing import Dict, Any
from app.models.domain import AgentPassport

class BlastRadiusCalculator:
    """Calculates financial exposure metrics for an agent passport."""
    
    @staticmethod
    def calculate_exposure(passport: AgentPassport) -> Dict[str, Any]:
        # Unmitigated potential daily exposure (e.g. 5 transactions without single limit cap)
        unmitigated_daily = 350000.0  # 5 x ₹70k+ unconstrained
        
        # Protected daily cap under IntentGate
        protected_max = float(passport.daily_spend_limit)
        
        saved_exposure = max(0.0, unmitigated_daily - protected_max)
        protection_percentage = round((saved_exposure / unmitigated_daily) * 100, 1) if unmitigated_daily > 0 else 100.0
        
        return {
            "agent_id": passport.agent_id,
            "unmitigated_daily_exposure": unmitigated_daily,
            "intentgate_protected_max_exposure": protected_max,
            "single_transaction_limit": passport.single_tx_limit,
            "max_daily_transactions": passport.max_daily_transactions,
            "recurring_allowed": passport.recurring_allowed,
            "protection_percentage": protection_percentage
        }

blast_radius_calculator = BlastRadiusCalculator()
