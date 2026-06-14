#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 6 Live eBay Sandbox API Integration - Valid SKU Format"""
import os
import json
import requests
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import re

@dataclass
class LiveListingResult:
    sku: str
    status: str
    listing_id: str = None
    offer_id: str = None
    error: str = None
    timestamp: str = None

class EBayLiveAPIClient:
    def __init__(self, user_token, sandbox=True):
        self.user_token = user_token
        self.sandbox = sandbox
        self.base_url = "https://api.sandbox.ebay.com" if sandbox else "https://api.ebay.com"
        self.timeout = 30
    
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Language": "en-US"
        }
    
    def create_inventory_item(self, sku, product_title, quantity=10, price=99.99):
        """Create an inventory item"""
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        
        payload = {
            "product": {
                "title": product_title,
                "description": "Test product from MarginScout"
            },
            "condition": "NEW",
            "availability": {
                "shipToLocationAvailability": {
                    "quantity": quantity
                }
            },
            "price": {
                "value": str(price),
                "currency": "USD"
            }
        }
        
        print(f"    [Inventory] Creating inventory item for SKU: {sku}")
        
        try:
            response = requests.put(url, json=payload, headers=self._get_headers(), timeout=self.timeout)
            print(f"    Response Status: {response.status_code}")
            
            if response.status_code in [200, 201, 204]:
                print(f"    OK: Inventory item created")
                return True, {"sku": sku, "status": "created"}
            else:
                error_msg = response.text
                print(f"    ERROR: {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            print(f"    ERROR: {error_msg}")
            return False, error_msg
    
    def create_offer(self, sku, listing_type="FIXED_PRICE", quantity_available=10):
        """Create an offer"""
        url = f"{self.base_url}/sell/inventory/v1/offer"
        
        payload = {
            "sku": sku,
            "listingType": listing_type,
            "format": "FIXED_PRICE",
            "quantityAvailable": quantity_available,
            "pricingSummary": {
                "price": {
                    "value": "99.99",
                    "currency": "USD"
                }
            },
            "marketplaceId": "EBAY_US",
            "categoryId": "27000"
        }
        
        print(f"    [Offer] Creating offer for SKU: {sku}")
        
        try:
            response = requests.post(url, json=payload, headers=self._get_headers(), timeout=self.timeout)
            print(f"    Response Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                offer_data = response.json()
                offer_id = offer_data.get('offerId', 'N/A')
                print(f"    OK: Offer created with ID: {offer_id}")
                return True, offer_id
            else:
                error_msg = response.text
                print(f"    ERROR: {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            print(f"    ERROR: {error_msg}")
            return False, error_msg
    
    def publish_offer(self, offer_id):
        """Publish an offer"""
        url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish"
        
        print(f"    [Publish] Publishing offer: {offer_id}")
        
        try:
            response = requests.post(url, headers=self._get_headers(), timeout=self.timeout)
            print(f"    Response Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                publish_data = response.json()
                listing_id = publish_data.get('listingId', 'N/A')
                print(f"    OK: Offer published with Listing ID: {listing_id}")
                return True, publish_data
            else:
                error_msg = response.text
                print(f"    ERROR: {error_msg}")
                return False, error_msg
        except Exception as e:
            error_msg = str(e)
            print(f"    ERROR: {error_msg}")
            return False, error_msg

class Phase6LiveIntegrationExecutor:
    def __init__(self, api_client):
        self.api_client = api_client
        self.results = []
    
    def generate_valid_sku(self):
        """Generate a valid SKU (alphanumeric, max 50 chars)"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        sku = f"MS{timestamp}001"
        return sku
    
    def execute_live_listing_creation(self, sku, product_title):
        """Execute complete listing creation workflow"""
        print(f"\nPhase 6: Live Listing Creation - {sku}")
        print("=" * 70)
        
        result = LiveListingResult(sku=sku, status="PENDING", timestamp=datetime.now().isoformat())
        
        # Step 1: Create Inventory Item
        print("[Step 1] Creating inventory item...")
        success, response = self.api_client.create_inventory_item(sku, product_title, quantity=10, price=99.99)
        if not success:
            result.status = "FAILED"
            result.error = str(response)
            self.results.append(result)
            print(f"\nResult: FAILED - {result.error}\n")
            return
        
        # Step 2: Create Offer
        print("\n[Step 2] Creating offer...")
        success, offer_id = self.api_client.create_offer(sku, quantity_available=10)
        if not success:
            result.status = "FAILED"
            result.error = f"Offer creation failed: {offer_id}"
            self.results.append(result)
            print(f"\nResult: FAILED - {result.error}\n")
            return
        
        result.offer_id = offer_id
        
        # Step 3: Publish Offer
        print(f"\n[Step 3] Publishing offer...")
        success, publish_response = self.api_client.publish_offer(offer_id)
        if not success:
            result.status = "FAILED"
            result.error = f"Publish failed: {publish_response}"
            self.results.append(result)
            print(f"\nResult: FAILED - {result.error}\n")
            return
        
        result.status = "SUCCESS"
        result.listing_id = publish_response.get('listingId', 'N/A')
        self.results.append(result)
        print(f"\nResult: SUCCESS\n")
    
    def get_summary(self):
        """Generate summary"""
        successful = len([r for r in self.results if r.status == "SUCCESS"])
        failed = len([r for r in self.results if r.status == "FAILED"])
        
        return {
            "total": len(self.results),
            "successful": successful,
            "failed": failed,
            "results": [asdict(r) for r in self.results]
        }

def load_oauth_config():
    """Load OAuth configuration from .env"""
    env_path = os.path.expanduser('~/.marginscount/.env')
    config = {
        'user_token': None,
        'sandbox': True
    }
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    if key == 'EBAY_REFRESH_TOKEN':
                        config['user_token'] = value
                    elif key == 'EBAY_ENV':
                        config['sandbox'] = value == 'sandbox'
    
    return config

def main():
    print("=" * 70)
    print("Phase 6 Live eBay Sandbox API Integration - Valid SKU Format")
    print("=" * 70)
    
    # Load configuration
    config = load_oauth_config()
    if not config['user_token']:
        print("ERROR: EBAY_REFRESH_TOKEN not found in .env")
        return
    
    print(f"\n[Step 0] Loading configuration...")
    print(f"  Environment: {'sandbox' if config['sandbox'] else 'production'}")
    print(f"  User Token: {config['user_token'][:40]}...")
    
    # Initialize API client
    print(f"\n[Step 1] Initializing API client...")
    api_client = EBayLiveAPIClient(config['user_token'], sandbox=config['sandbox'])
    print("  OK: API client initialized")
    
    # Initialize executor
    print(f"\n[Step 2] Initializing executor...")
    executor = Phase6LiveIntegrationExecutor(api_client)
    print("  OK: Executor initialized")
    
    # Execute live listing creation
    print(f"\n[Step 3] Executing live listing creation...")
    sku = executor.generate_valid_sku()
    print(f"  Generated valid SKU: {sku}")
    executor.execute_live_listing_creation(sku, "MarginScout Test Product")
    
    # Generate report
    print("\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
    
    summary = executor.get_summary()
    print(f"\nSuccessful: {summary['successful']}/{summary['total']}")
    print(f"Failed: {summary['failed']}/{summary['total']}")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS" if summary['failed'] == 0 else "PARTIAL_SUCCESS" if summary['successful'] > 0 else "FAILED",
        **summary
    }
    
    report_path = Path("PHASE6_LIVE_API_TEST_RESULT.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved: {report_path}")

if __name__ == '__main__':
    main()
