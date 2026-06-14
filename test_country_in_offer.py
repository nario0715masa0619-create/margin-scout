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

sku = "MSCOUNTRYTEST001"

# Offer with country field
payload = {
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
    "country": "US"
}

url = f"{base_url}/sell/inventory/v1/offer"
print("Creating offer WITH country field...")
print(f"Payload: {json.dumps(payload, indent=2)}")

response = requests.post(url, json=payload, headers=headers, timeout=30)
print(f"\nStatus: {response.status_code}")
print(f"Response: {response.text[:500]}")

if response.status_code == 201:
    offer_data = response.json()
    offer_id = offer_data.get('offerId')
    print(f"\nOffer created: {offer_id}")
    
    # Try to publish this one
    print(f"\nNow trying to publish...")
    pub_url = f"{base_url}/sell/inventory/v1/offer/{offer_id}/publish"
    pub_response = requests.post(pub_url, headers=headers, timeout=30)
    print(f"Publish Status: {pub_response.status_code}")
    print(f"Publish Response: {pub_response.text[:500]}")
