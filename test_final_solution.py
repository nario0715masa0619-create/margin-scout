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

sku = "MSFINAL001"

# Step 1: Create Inventory
print("[Step 1] Creating Inventory Item...")
inv_url = f"{base_url}/sell/inventory/v1/inventory_item/{sku}"
inv_payload = {
    "product": {"title": "Final Test", "description": "Test"},
    "condition": "NEW",
    "availability": {"shipToLocationAvailability": {"quantity": 10}},
    "price": {"value": "99.99", "currency": "USD"}
}

inv_response = requests.put(inv_url, json=inv_payload, headers=headers, timeout=30)
print(f"Status: {inv_response.status_code}")

if inv_response.status_code not in [200, 201, 204]:
    print(f"ERROR: {inv_response.text}")
    sys.exit(1)

# Step 2: Create Offer with ALL REQUIRED fields
print("\n[Step 2] Creating Offer with ALL required fields...")
offer_url = f"{base_url}/sell/inventory/v1/offer"

offer_payload = {
    "sku": sku,
    "listingType": "FIXED_PRICE",
    "format": "FIXED_PRICE",
    "quantityAvailable": 10,
    "pricingSummary": {
        "price": {
            "value": "99.99",
            "currency": "USD"
        }
    },
    "marketplaceId": "EBAY_US",
    "categoryId": "27000",
    "listingDuration": "GTC",
    "listingPolicies": {
        "paymentPolicyId": "PAYMENT_POLICY_ID",
        "returnPolicyId": "RETURN_POLICY_ID",
        "fulfillmentPolicyId": "FULFILLMENT_POLICY_ID"
    },
    "merchantLocationKey": "DEFAULT"
}

print(f"Payload:\n{json.dumps(offer_payload, indent=2)}")
offer_response = requests.post(offer_url, json=offer_payload, headers=headers, timeout=30)
print(f"Status: {offer_response.status_code}")

if offer_response.status_code == 201:
    offer_data = offer_response.json()
    offer_id = offer_data.get('offerId')
    print(f"Offer created: {offer_id}")
    
    # Step 3: Publish with NO request body
    print(f"\n[Step 3] Publishing Offer {offer_id}...")
    pub_url = f"{base_url}/sell/inventory/v1/offer/{offer_id}/publish"
    pub_response = requests.post(pub_url, headers=headers, timeout=30)
    print(f"Status: {pub_response.status_code}")
    
    if pub_response.status_code in [200, 201]:
        print("SUCCESS!")
        print(f"Response:\n{json.dumps(pub_response.json(), indent=2)}")
    else:
        print(f"ERROR: {pub_response.text}")
else:
    print(f"Offer creation failed:\n{offer_response.text}")
