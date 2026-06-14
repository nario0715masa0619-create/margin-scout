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

sku = "MSCOUNTRYTEST002"

# Step 1: Create Inventory Item
print("[Step 1] Creating Inventory Item...")
inv_url = f"{base_url}/sell/inventory/v1/inventory_item/{sku}"
inv_payload = {
    "product": {
        "title": "Test Product",
        "description": "Test"
    },
    "condition": "NEW",
    "availability": {
        "shipToLocationAvailability": {
            "quantity": 10
        }
    },
    "price": {
        "value": "99.99",
        "currency": "USD"
    }
}

inv_response = requests.put(inv_url, json=inv_payload, headers=headers, timeout=30)
print(f"Inventory Status: {inv_response.status_code}")

if inv_response.status_code not in [200, 201, 204]:
    print(f"ERROR: {inv_response.text}")
    sys.exit(1)

# Step 2: Create Offer WITH country
print("\n[Step 2] Creating Offer WITH country field...")
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
    "country": "US"
}

print(f"Offer Payload: {json.dumps(offer_payload, indent=2)}")
offer_response = requests.post(offer_url, json=offer_payload, headers=headers, timeout=30)
print(f"Offer Status: {offer_response.status_code}")

if offer_response.status_code == 201:
    offer_data = offer_response.json()
    offer_id = offer_data.get('offerId')
    print(f"Offer created: {offer_id}")
    
    # Step 3: Publish
    print(f"\n[Step 3] Publishing Offer {offer_id}...")
    pub_url = f"{base_url}/sell/inventory/v1/offer/{offer_id}/publish"
    pub_response = requests.post(pub_url, headers=headers, timeout=30)
    print(f"Publish Status: {pub_response.status_code}")
    
    if pub_response.status_code in [200, 201]:
        print("SUCCESS! Listing published!")
        print(f"Response: {json.dumps(pub_response.json(), indent=2)}")
    else:
        print(f"Publish Error: {pub_response.text}")
else:
    print(f"Offer Error: {offer_response.text}")
