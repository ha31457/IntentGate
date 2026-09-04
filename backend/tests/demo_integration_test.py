import httpx
import json
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
BASE_URL = "http://localhost:8000/api/v1"

def run_demo_readiness_test():
    client = httpx.Client(timeout=10.0)
    print("--- STARTING DEMO READINESS INTEGRATION AUDIT ---")
    
    # 1. Intent Extraction
    extract_resp = client.post(f"{BASE_URL}/intents/extract", json={
        "user_prompt": "Find me a good laptop for programming under ₹70,000. Buy it if you find one that meets my requirements.",
        "agent_id": "agent_shopping_alpha"
    })
    print("\n1. INTENT EXTRACTION RESPONSE STATUS:", extract_resp.status_code)
    intent_data = extract_resp.json()
    print("Extracted Intent ID:", intent_data["intent_id"])
    print("HMAC Fingerprint:", intent_data["fingerprint"])
    print("Max Budget:", intent_data["max_budget"])
    
    intent_id = intent_data["intent_id"]
    fingerprint = intent_data["fingerprint"]
    
    # 2. Normal Transaction (Pass) - ₹68,999 with fresh idempotency key
    idemp_1 = f"live_idemp_{int(time.time()*1000)}_1"
    tx1_resp = client.post(f"{BASE_URL}/transactions/authorize", json={
        "agent_id": "agent_shopping_alpha",
        "intent_id": intent_id,
        "intent_fingerprint": fingerprint,
        "product_id": "prod_devbook_pro",
        "proposed_price": 68999.0,
        "proposed_quantity": 1,
        "idempotency_key": idemp_1
    })
    print("\n2. NORMAL TRANSACTION STATUS:", tx1_resp.status_code)
    tx1_data = tx1_resp.json()
    print("Decision:", tx1_data["decision"])
    print("Status:", tx1_data["status"])
    print("Block Reason:", tx1_data.get("block_reason"))
    print("Razorpay Order ID:", tx1_data.get("razorpay_order_id"))
    
    # 3. Intent Drift Transaction (Block due to budget violation) - ₹72,999
    idemp_2 = f"live_idemp_{int(time.time()*1000)}_2"
    tx2_resp = client.post(f"{BASE_URL}/transactions/authorize", json={
        "agent_id": "agent_shopping_alpha",
        "intent_id": intent_id,
        "intent_fingerprint": fingerprint,
        "product_id": "prod_ultradev_x",
        "proposed_price": 72999.0,
        "proposed_quantity": 1,
        "idempotency_key": idemp_2
    })
    print("\n3. INTENT DRIFT TRANSACTION (BLOCK) STATUS:", tx2_resp.status_code)
    tx2_data = tx2_resp.json()
    print("Decision:", tx2_data["decision"])
    print("Block Reason:", tx2_data.get("block_reason"))
    print("Price Variance:", tx2_data.get("price_variance"))
    blocked_tx_id = tx2_data["transaction_id"]
    
    # 4. Chaos Injection (PRICE_CHANGED)
    chaos_resp = client.post(f"{BASE_URL}/chaos/inject", json={
        "scenario_id": "PRICE_CHANGED",
        "active": True
    })
    print("\n4. CHAOS INJECTION STATUS:", chaos_resp.status_code, chaos_resp.json())
    
    idemp_3 = f"live_idemp_{int(time.time()*1000)}_3"
    tx_chaos_resp = client.post(f"{BASE_URL}/transactions/authorize", json={
        "agent_id": "agent_shopping_alpha",
        "intent_id": intent_id,
        "intent_fingerprint": fingerprint,
        "product_id": "prod_devbook_pro",
        "proposed_price": 68999.0, # Attempt 68999, but Chaos will force 72999
        "proposed_quantity": 1,
        "idempotency_key": idemp_3
    })
    print("CHAOS TRANSACTION DECISION:", tx_chaos_resp.json()["decision"], "| Reason:", tx_chaos_resp.json()["block_reason"])
    
    # Reset Chaos
    client.post(f"{BASE_URL}/chaos/reset", json={})
    
    # 5. Replay Timeline Audit
    replay_resp = client.get(f"{BASE_URL}/transactions/{blocked_tx_id}/replay")
    print("\n5. REPLAY ENDPOINT STATUS:", replay_resp.status_code)
    replay_data = replay_resp.json()
    print("Replay Events Count:", len(replay_data["events"]))
    for ev in replay_data["events"]:
        print(f"   [{ev['timestamp']}] {ev['stage']} | Actor: {ev['actor']} | Decision: {ev['decision']} -> {ev['reason']}")

if __name__ == "__main__":
    run_demo_readiness_test()
