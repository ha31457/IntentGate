import hashlib
import hmac
import json
from typing import Dict, Any

def normalize_intent_dict(intent_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministically normalizes an intent payload.
    Sorts dictionary keys, strips whitespace, converts strings to lower case where applicable.
    """
    normalized = {}
    for key in sorted(intent_data.keys()):
        val = intent_data[key]
        if isinstance(val, str):
            normalized[key] = val.strip()
        elif isinstance(val, list):
            normalized[key] = sorted([v.strip() if isinstance(v, str) else v for v in val])
        elif isinstance(val, dict):
            normalized[key] = normalize_intent_dict(val)
        else:
            normalized[key] = val
    return normalized

def generate_intent_fingerprint(intent_data: Dict[str, Any], user_secret: str = "user_demo_secret") -> str:
    """
    Generates a deterministic HMAC-SHA256 fingerprint for a canonical intent object salted with a user secret.
    """
    normalized = normalize_intent_dict(intent_data)
    canonical_json = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
    return hmac.new(user_secret.encode('utf-8'), canonical_json.encode('utf-8'), hashlib.sha256).hexdigest()

def verify_razorpay_signature(body: bytes, signature: str, secret: str) -> bool:
    """
    Verifies Razorpay Webhook HMAC-SHA256 signature.
    """
    if not signature or not secret:
        return False
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)
