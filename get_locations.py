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

print("Fetching merchant locations...")

url = f"{base_url}/sell/inventory/v1/location"
response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}")
