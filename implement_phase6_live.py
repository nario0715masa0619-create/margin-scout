#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 6: Live API Implementation (REAL Sandbox API Calls)
Creates actual eBay Sandbox listings via Inventory -> Offer -> Publish flow
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Optional, Dict
from dataclasses import dataclass, asdict

sys.path.insert(0, os.getcwd())

try:
    from src.config_loader import ConfigLoader
    from src.api_integration.oauth_handler import EBayOAuthConfig, EBayOAuthHandler
except ImportError as e:
    print(f"WARNING: Import failed: {e}")
    print("Continuing with basic OAuth config...")

# ============================================================================
# Data Models
# ============================================================================

@dataclass
class LiveListingResult:
    """Result of live listing creation"""
    sku: str
    status: str
    inventory_item_id: Optional[str] = None
    offer_id: Optional[str] = None
    listing_id: Optional[str] = None
    item_url: Optional[str] = None
    errors: list = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

# ============================================================================
# eBay Live API Client (REAL Implementation)
# ============================================================================

class EBayLiveAPIClient:
    """eBay Live API Client - Makes REAL API calls to Sandbox"""
    
    def __init__(self, oauth_handler, api_config):
        self.oauth_handler = oauth_handler
        self.api_config = api_config
        self.base_url = "https://api.sandbox.ebay.com"
    
    def _get_headers(self) -> Dict:
        """Get authenticated headers"""
        try:
            token = self.oauth_handler.get_access_token()
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        except Exception as e:
            print(f"ERROR: Failed to get access token: {e}")
            return None
    
    def create_inventory_item(self, sku: str, product_data: Dict) -> Dict:
        """Create inventory item via PUT /sell/inventory/v1/inventory_item/{sku}"""
        print(f"\n  [Inventory] Creating inventory item for SKU: {sku}")
        
        headers = self._get_headers()
        if not headers:
            return {'status': 'ERROR', 'error': 'Failed to get auth token'}
        
        url = f"{self.base_url}/sell/inventory/v1/inventory_item/{sku}"
        
        payload = {
            "product": {
                "title": product_data.get('title', 'Product Title'),
                "description": product_data.get('description', 'Product Description'),
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
                headers=headers,
                json=payload,
                timeout=30,
            )
            
            print(f"    HTTP Status: {response.status_code}")
            
            if response.status_code in [200, 201, 204]:
                print(f"    OK: Inventory item created")
                return {
                    'status': 'SUCCESS',
                    'sku': sku,
                    'status_code': response.status_code,
                    'response': response.json() if response.text else {},
                }
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                print(f"    ERROR: {error_msg}")
                return {
                    'status': 'FAILED',
                    'error': error_msg,
                    'status_code': response.status_code,
                }
        
        except requests.RequestException as e:
            print(f"    ERROR: Request failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def create_offer(self, sku: str, price: float) -> Dict:
        """Create offer via POST /sell/inventory/v1/offer"""
        print(f"\n  [Offer] Creating offer for SKU: {sku} at ${price}")
        
        headers = self._get_headers()
        if not headers:
            return {'status': 'ERROR', 'error': 'Failed to get auth token'}
        
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
                headers=headers,
                json=payload,
                timeout=30,
            )
            
            print(f"    HTTP Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                data = response.json()
                offer_id = data.get('offerId')
                print(f"    OK: Offer created (ID: {offer_id})")
                return {
                    'status': 'SUCCESS',
                    'sku': sku,
                    'offer_id': offer_id,
                    'status_code': response.status_code,
                    'response': data,
                }
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                print(f"    ERROR: {error_msg}")
                return {
                    'status': 'FAILED',
                    'error': error_msg,
                    'status_code': response.status_code,
                }
        
        except requests.RequestException as e:
            print(f"    ERROR: Request failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def publish_offer(self, offer_id: str) -> Dict:
        """Publish offer via POST /sell/inventory/v1/offer/{offerId}/publish"""
        print(f"\n  [Publish] Publishing offer: {offer_id}")
        
        headers = self._get_headers()
        if not headers:
            return {'status': 'ERROR', 'error': 'Failed to get auth token'}
        
        url = f"{self.base_url}/sell/inventory/v1/offer/{offer_id}/publish"
        
        try:
            print(f"    URL: {url}")
            response = requests.post(
                url,
                headers=headers,
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
                return {
                    'status': 'SUCCESS',
                    'offer_id': offer_id,
                    'listing_id': listing_id,
                    'item_url': item_url,
                    'status_code': response.status_code,
                    'response': data,
                }
            else:
                error_msg = response.text if response.text else f"HTTP {response.status_code}"
                print(f"    ERROR: {error_msg}")
                return {
                    'status': 'FAILED',
                    'error': error_msg,
                    'status_code': response.status_code,
                }
        
        except requests.RequestException as e:
            print(f"    ERROR: Request failed: {e}")
            return {'status': 'ERROR', 'error': str(e)}

# ============================================================================
# Phase 6 Live Integration Executor
# ============================================================================

class Phase6LiveIntegrationExecutor:
    """Orchestrates live API calls"""
    
    def __init__(self, api_client: EBayLiveAPIClient):
        self.api_client = api_client
        self.results = []
    
    def execute_live_listing(self, sku: str, product_data: Dict, price: float) -> LiveListingResult:
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

# ============================================================================
# OAuth Handler (Basic implementation)
# ============================================================================

class BasicOAuthHandler:
    """Basic OAuth handler for testing"""
    
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = None
    
    def get_access_token(self):
        """Get access token using refresh token"""
        if self.access_token:
            return self.access_token
        
        url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        
        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
        }
        
        try:
            response = requests.post(
                url,
                auth=(self.client_id, self.client_secret),
                data=payload,
                timeout=10,
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                return self.access_token
            else:
                print(f"WARNING: Token refresh returned {response.status_code}")
                print(f"Response: {response.text}")
                return None
        
        except Exception as e:
            print(f"ERROR: Token refresh failed: {e}")
            return None

# ============================================================================
# Main Execution
# ============================================================================

def main():
    print("\n" + "="*80)
    print("MarginScout Phase 6: LIVE API Implementation (Real Sandbox Calls)")
    print("="*80)
    
    # Load config from .env
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
    
    client_id = config.get('EBAY_CLIENT_ID')
    client_secret = config.get('EBAY_CLIENT_SECRET')
    refresh_token = config.get('EBAY_REFRESH_TOKEN')
    
    print(f"  Environment: {config.get('EBAY_ENV', 'sandbox')}")
    print(f"  Client ID: {client_id[:20] if client_id else 'NOT SET'}...")
    print(f"  Refresh Token: {refresh_token[:20] if refresh_token else 'NOT SET'}...")
    
    if not client_id or not client_secret or not refresh_token:
        print("\n  ERROR: Missing required configuration")
        sys.exit(1)
    
    # Initialize OAuth handler
    print("\n[Step 1] Initializing OAuth handler...")
    oauth_handler = BasicOAuthHandler(client_id, client_secret, refresh_token)
    print("  OK: OAuth handler initialized")
    
    # Initialize API client
    print("\n[Step 2] Initializing API client...")
    class APIConfig:
        base_url = "https://api.sandbox.ebay.com"
        timeout = 30
    
    api_client = EBayLiveAPIClient(oauth_handler, APIConfig())
    print("  OK: API client initialized")
    
    # Initialize executor
    print("\n[Step 3] Initializing executor...")
    executor = Phase6LiveIntegrationExecutor(api_client)
    print("  OK: Executor initialized")
    
    # Execute live listing creation
    print("\n[Step 4] Executing live listing creation...")
    
    test_items = [
        {
            'sku': f'MARGIN-SANDBOX-{datetime.now().strftime("%Y%m%d%H%M%S")}-001',
            'title': 'Test Product - MarginScout',
            'description': 'This is a test product created by MarginScout Phase 6',
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
        'phase': 'Phase 6 - Live API Integration',
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
    sys.exit(main())
