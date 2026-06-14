import requests
import json
import sys

user_token = sys.argv[1]
offer_id = "11165321010"
base_url = "https://api.sandbox.ebay.com"

headers = {
    "Authorization": f"Bearer {user_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Content-Language": "en-US"
}

url = f"{base_url}/sell/inventory/v1/offer/{offer_id}/publish"

# 複数のペイロードパターンを試す
payloads = [
    { "marketplaceId": "EBAY_US" },
    { "marketplaceId": "EBAY_US", "country": "US" },
    { "region": { "country": "US" } },
    { "item": { "country": "US" } },
]

for i, payload in enumerate(payloads):
    print(f"\n--- Attempt {i+1} ---")
    print(f"Payload: {json.dumps(payload)}")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code >= 400:
        print(f"Error: {response.text[:200]}")
    else:
        print(f"Success: {response.text[:200]}")
