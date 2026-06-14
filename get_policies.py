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

print("Fetching seller policies...")

# Get Payment Policies
print("\n[1] Payment Policies")
url = f"{base_url}/sell/account/v1/payment_policy"
response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2)[:1000])
    if data.get('paymentPolicies'):
        print(f"Found {len(data['paymentPolicies'])} payment policies")
        for p in data['paymentPolicies'][:1]:
            print(f"  - {p.get('name')} (ID: {p.get('paymentPolicyId')})")

# Get Return Policies
print("\n[2] Return Policies")
url = f"{base_url}/sell/account/v1/return_policy"
response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if data.get('returnPolicies'):
        print(f"Found {len(data['returnPolicies'])} return policies")
        for p in data['returnPolicies'][:1]:
            print(f"  - {p.get('name')} (ID: {p.get('returnPolicyId')})")

# Get Fulfillment Policies
print("\n[3] Fulfillment Policies")
url = f"{base_url}/sell/account/v1/fulfillment_policy"
response = requests.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    if data.get('fulfillmentPolicies'):
        print(f"Found {len(data['fulfillmentPolicies'])} fulfillment policies")
        for p in data['fulfillmentPolicies'][:1]:
            print(f"  - {p.get('name')} (ID: {p.get('fulfillmentPolicyId')})")
