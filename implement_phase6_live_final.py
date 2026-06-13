#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 6: Live API Implementation (Direct User Token - Fixed)
"""

import os
import json
import requests
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class LiveListingResult:
    sku: str
    status: str
    inventory_item_id: str = None
    offer_id: str = None
    listing_id: str = None
    item_url: str = None
    errors: list = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class EBayLiveAPIClient:
    """eBay Live API Client using User Token"""
    
    def __init__(self, user_token):
        self.user_token = user_token
        self.base_url = "https://api.sandbox.ebay.com"
    
    def _get_headers(self):
        """Get authenticated headers with Content-Language"""
        return {
            'Authorization': f'Bearer {self.user_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Content-Language': 'en-US',
        }
    
    def create_inventory_item(self, sku, product_data):
        """Create inventory item"""
        print(f"\n  [Inventory] Creating inventory item for SKU: {sku}")
        
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        
        payload = {
            "product": {
                "title": product_data.get('title', 'Product'),
                "description": product_data.get('description', 'Description'),
            },
            "condition": "NEW",
            "availability": {
                "quantity": 10
            }
        }
        
        try:
            print(f"    URL: {url}")
            response = requests.put(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )
            
            print(f"    HTTP Status: {response.status_code}")
            
            if response.status_code in [200, 201, 204]:
                print(f"    OK: Inventory item created")
                return {'status': 'SUCCESS', 'sku': sku}
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                print(f"    ERROR: {error_msg}")
                return {'status': 'FAILED', 'error': error_msg, 'status_code': response.status_code}
        
        except Exception as e:
            print(f"    ERROR: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def create_offer(self, sku, price):
        """Create offer"""
        print(f"\n  [Offer] Creating offer for SKU: {sku} at ${price}")
        
        url = f"{self.base_url}/sell/inventory/v1/offer"
        
        payload = {
            "sku": sku,
            "listingFormat": "FIXED_PRICE",
            "pricingSummary": {
                "price": {
                    "currency": "USD",
                    "value": str(price)
                }
            },
            "merchantLocationKey": "default"
        }
        
        try:
            print(f"    URL: {url}")
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )
            
            print(f"    HTTP Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                offer_id = data.get('offerId')
                print(f"    OK: Offer created (ID: {offer_id})")
                return {'status': 'SUCCESS', 'offer_id': offer_id}
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                print(f"    ERROR: {error_msg}")
                return {'status': 'FAILED', 'error': error_msg, 'status_code': response.status_code}
        
        except Exception as e:
            print(f"    ERROR: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def publish_offer(self, offer_id):
        """Publish offer"""
        print(f"\n  [Publish] Publishing offer: {offer_id}")
        
        url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish"
        
        try:
            print(f"    URL: {url}")
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={},
                timeout=30,
            )
            
            print(f"    HTTP Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                listing_id = data.get('listingId')
                item_url = data.get('itemUrl')
                print(f"    OK: Offer published")
                print(f"        Listing ID: {listing_id}")
                print(f"        Item URL: {item_url}")
                return {'status': 'SUCCESS', 'listing_id': listing_id, 'item_url': item_url}
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                print(f"    ERROR: {error_msg}")
                return {'status': 'FAILED', 'error': error_msg, 'status_code': response.status_code}
        
        except Exception as e:
            print(f"    ERROR: {e}")
            return {'status': 'ERROR', 'error': str(e)}

class Phase6LiveIntegrationExecutor:
    """Orchestrates live API calls"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.results = []
    
    def execute_live_listing(self, sku, product_data, price):
        """Execute full live listing creation flow"""
        print("\n" + "="*70)
        print(f"Phase 6: Live Listing Creation - {sku}")
        print("="*70)
        
        result = LiveListingResult(
            sku=sku,
            status='PENDING',
            timestamp=datetime.now().isoformat(),
        )
        
        # Step 1: Create inventory item
        print("\n[Step 1] Creating inventory item...")
        inv_result = self.api_client.create_inventory_item(sku, product_data)
        
        if inv_result['status'] != 'SUCCESS':
            result.status = 'FAILED'
            result.errors.append(f"Inventory creation failed: {inv_result.get('error')}")
            return result
        
        result.inventory_item_id = sku
        
        # Step 2: Create offer
        print("\n[Step 2] Creating offer...")
        offer_result = self.api_client.create_offer(sku, price)
        
        if offer_result['status'] != 'SUCCESS':
            result.status = 'FAILED'
            result.errors.append(f"Offer creation failed: {offer_result.get('error')}")
            return result
        
        result.offer_id = offer_result.get('offer_id')
        
        # Step 3: Publish offer
        print("\n[Step 3] Publishing offer...")
        publish_result = self.api_client.publish_offer(result.offer_id)
        
        if publish_result['status'] != 'SUCCESS':
            result.status = 'FAILED'
            result.errors.append(f"Offer publish failed: {publish_result.get('error')}")
            return result
        
        result.listing_id = publish_result.get('listing_id')
        result.item_url = publish_result.get('item_url')
        result.status = 'SUCCESS'
        
        print("\n" + "="*70)
        print(f"Result: {result.status}")
        print("="*70)
        
        self.results.append(result)
        return result

def main():
    print("\n" + "="*80)
    print("MarginScout Phase 6: LIVE API Implementation (Direct User Token - Final)")
    print("="*80)
    
    # Load config
    print("\n[Step 0] Loading configuration from .env...")
    env_path = os.path.expanduser('~/.marginscount/.env')
    
    config = {}
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    config[key] = value
    
    user_token = config.get('EBAY_REFRESH_TOKEN')
    
    print(f"  Environment: {config.get('EBAY_ENV', 'sandbox')}")
    print(f"  User Token: {user_token[:30] if user_token else 'NOT SET'}...")
    
    if not user_token:
        print("\n  ERROR: EBAY_REFRESH_TOKEN not set")
        return 1
    
    # Initialize API client
    print("\n[Step 1] Initializing API client with User Token...")
    api_client = EBayLiveAPIClient(user_token)
    print("  OK: API client initialized")
    
    # Initialize executor
    print("\n[Step 2] Initializing executor...")
    executor = Phase6LiveIntegrationExecutor(api_client)
    print("  OK: Executor initialized")
    
    # Execute live listing creation
    print("\n[Step 3] Executing live listing creation...")
    
    test_items = [
        {
            'sku': f'MARGIN-SANDBOX-{datetime.now().strftime("%Y%m%d%H%M%S")}-001',
            'title': 'Test Product - MarginScout Live API',
            'description': 'MarginScout Phase 6 Live eBay Sandbox API Test',
            'price': 29.99,
        },
    ]
    
    results = []
    for item in test_items:
        result = executor.execute_live_listing(
            sku=item['sku'],
            product_data={'title': item['title'], 'description': item['description']},
            price=item['price'],
        )
        results.append(asdict(result))
    
    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'phase': 'Phase 6 - Live API Integration (Direct User Token)',
        'environment': config.get('EBAY_ENV', 'sandbox'),
        'test_count': len(results),
        'successful': len([r for r in results if r['status'] == 'SUCCESS']),
        'failed': len([r for r in results if r['status'] != 'SUCCESS']),
        'results': results,
    }
    
    with open('PHASE6_LIVE_API_TEST_RESULT.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print("Test Complete")
    print("="*80)
    print(f"\nSuccessful: {output['successful']}/{output['test_count']}")
    print(f"Failed: {output['failed']}/{output['test_count']}")
    print(f"\nReport saved: PHASE6_LIVE_API_TEST_RESULT.json\n")
    
    return 0 if output['failed'] == 0 else 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
