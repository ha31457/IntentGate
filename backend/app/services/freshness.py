import time
from datetime import datetime
from app.core.config import settings

class FreshnessGuardService:
    """Verifies that financial data (price/stock) meets freshness requirements."""
    
    @staticmethod
    def is_fresh(updated_at: datetime, max_age_seconds: int = settings.MAX_PRICE_DATA_AGE_SECONDS) -> bool:
        if not updated_at:
            return False
        age = (datetime.utcnow() - updated_at).total_seconds()
        return age <= max_age_seconds

    @staticmethod
    def get_data_age_seconds(updated_at: datetime) -> float:
        if not updated_at:
            return 999999.0
        return (datetime.utcnow() - updated_at).total_seconds()
