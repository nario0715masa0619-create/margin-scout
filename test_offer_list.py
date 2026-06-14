import requests
import json
import sys

user_token = sys.argv[1]
base_url = "https://api.sandbox.ebay.com"

headers = {
    "Authorization": f"Bearer {user_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Content-Language": "en-US"
}

print(f"Token (first 50): {user_token[:50]}...")
print(f"Making request to: {base_url}/sell/inventory/v1/offer")

# Offer 一覧を取得
url = f"{base_url}/sell/inventory/v1/offer"
response = requests.get(url, headers=headers, timeout=30)

print(f"\nStatus: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")
