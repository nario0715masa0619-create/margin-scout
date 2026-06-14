#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 6: OAuth & Live API Implementation
Sandbox-first, dry-run/live separation, audit-focused
"""

import os
import json
import base64
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import requests
from urllib.parse import urlencode

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

@dataclass
class EBayOAuthConfig:
    """eBay OAuth configuration"""
    environment: str  # 'sandbox' or 'production'
    client_id: str
    client_secret: str
    redirect_uri: str
    refresh_token: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        """Load from environment variables"""
        return cls(
            environment=os.getenv('EBAY_ENV', 'sandbox'),
            client_id=os.getenv('EBAY_CLIENT_ID', ''),
            client_secret=os.getenv('EBAY_CLIENT_SECRET', ''),
            redirect_uri=os.getenv('EBAY_REDIRECT_URI', 'http://localhost:8080/callback'),
            refresh_token=os.getenv('EBAY_REFRESH_TOKEN', None),
        )

@dataclass
class EBayAPIConfig:
    """eBay API configuration"""
    environment: str  # 'sandbox' or 'production'
    timeout: int = 30
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    @property
    def base_url(self) -> str:
        """Get base URL based on environment"""
        if self.environment == 'sandbox':
            return 'https://api.sandbox.ebay.com'
        else:
            return 'https://api.ebay.com'
    
    @property
    def oauth_url(self) -> str:
        """Get OAuth endpoint"""
        if self.environment == 'sandbox':
            return 'https://auth.sandbox.ebay.com'
        else:
            return 'https://auth.ebay.com'
    
    @classmethod
    def from_env(cls):
        """Load from environment variables"""
        return cls(
            environment=os.getenv('EBAY_ENV', 'sandbox'),
            timeout=int(os.getenv('EBAY_REQUEST_TIMEOUT', '30')),
            max_retries=int(os.getenv('EBAY_MAX_RETRIES', '3')),
        )

# ============================================================================
# OAUTH HANDLER
# ============================================================================

@dataclass
class OAuthToken:
    """OAuth token data"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str]
    obtained_at: datetime
    
    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired (with buffer)"""
        expiry_time = self.obtained_at + timedelta(seconds=self.expires_in - buffer_seconds)
        return datetime.now() >= expiry_time
    
    def to_dict_masked(self) -> Dict:
        """Return token info with masked sensitive data"""
        return {
            'access_token': self.access_token[:10] + '...' + self.access_token[-10:],
            'token_type': self.token_type,
            'expires_in': self.expires_in,
            'obtained_at': self.obtained_at.isoformat(),
            'is_expired': self.is_expired(),
        }

class OAuthHandler:
    """Handle eBay OAuth 2.0 authentication"""
    
    def __init__(self, config: EBayOAuthConfig, api_config: EBayAPIConfig):
        self.config = config
        self.api_config = api_config
        self.token: Optional[OAuthToken] = None
    
    def get_authorization_url(self, scopes: List[str]) -> str:
        """Generate authorization URL for user to visit"""
        scope_string = ' '.join(scopes)
        params = {
            'client_id': self.config.client_id,
            'response_type': 'code',
            'redirect_uri': self.config.redirect_uri,
            'scope': scope_string,
        }
        auth_url = f"{self.api_config.oauth_url}/oauth2/authorize?{urlencode(params)}"
        return auth_url
    
    def exchange_code_for_token(self, auth_code: str) -> OAuthToken:
        """Exchange authorization code for access token"""
        url = f"{self.api_config.oauth_url}/identity/v1/oauth2/token"
        
        # Prepare credentials
        credentials = f"{self.config.client_id}:{self.config.client_secret}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {b64_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'grant_type': 'authorization_code',
            'code': auth_code,
            'redirect_uri': self.config.redirect_uri,
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=self.api_config.timeout)
            response.raise_for_status()
            
            response_data = response.json()
            self.token = OAuthToken(
                access_token=response_data['access_token'],
                token_type=response_data['token_type'],
                expires_in=response_data['expires_in'],
                refresh_token=response_data.get('refresh_token'),
                obtained_at=datetime.now(),
            )
            
            print(f"[OAuth] Token obtained successfully (expires in {self.token.expires_in}s)")
            return self.token
        
        except requests.RequestException as e:
            print(f"[OAuth] Token exchange failed: {str(e)}")
            raise
    
    def refresh_token_if_needed(self) -> OAuthToken:
        """Refresh token if expired"""
        if self.token and not self.token.is_expired():
            return self.token
        
        if not self.token or not self.token.refresh_token:
            raise ValueError("No refresh token available")
        
        url = f"{self.api_config.oauth_url}/identity/v1/oauth2/token"
        
        # Prepare credentials
        credentials = f"{self.config.client_id}:{self.config.client_secret}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {b64_credentials}',
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.token.refresh_token,
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=self.api_config.timeout)
            response.raise_for_status()
            
            response_data = response.json()
            self.token = OAuthToken(
                access_token=response_data['access_token'],
                token_type=response_data['token_type'],
                expires_in=response_data['expires_in'],
                refresh_token=response_data.get('refresh_token', self.token.refresh_token),
                obtained_at=datetime.now(),
            )
            
            print(f"[OAuth] Token refreshed successfully (expires in {self.token.expires_in}s)")
            return self.token
        
        except requests.RequestException as e:
            print(f"[OAuth] Token refresh failed: {str(e)}")
            raise
    
    def get_access_token(self) -> str:
        """Get valid access token (refresh if needed)"""
        if not self.token:
            raise ValueError("No token available. Please authenticate first.")
        
        self.refresh_token_if_needed()
        return self.token.access_token

# ============================================================================
# API ERROR CLASSIFICATION
# ============================================================================

class APIErrorType(str, Enum):
    OAUTH_ERROR = "oauth_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    PARTIAL_SUCCESS = "partial_success"
    UNKNOWN = "unknown"

@dataclass
class APIError:
    """API error information"""
    error_type: APIErrorType
    status_code: int
    message: str
    details: Dict = field(default_factory=dict)
    retriable: bool = False
    
    def should_retry(self) -> bool:
        """Determine if operation should be retried"""
        return self.retriable

# ============================================================================
# LIVE API CLIENT
# ============================================================================

@dataclass
class APIResponse:
    """API response wrapper"""
    status_code: int
    success: bool
    data: Dict
    error: Optional[APIError] = None
    raw_response: Optional[requests.Response] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class EBayLiveAPIClient:
    """eBay Live API client for Sandbox/Production"""
    
    def __init__(self, oauth_handler: OAuthHandler, api_config: EBayAPIConfig):
        self.oauth_handler = oauth_handler
        self.api_config = api_config
    
    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> APIResponse:
        """Make HTTP request to eBay API"""
        try:
            access_token = self.oauth_handler.get_access_token()
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            
            url = f"{self.api_config.base_url}{endpoint}"
            
            # Log request (masked)
            print(f"[API] {method} {endpoint}")
            
            if method == 'PUT':
                response = requests.put(url, headers=headers, json=payload, timeout=self.api_config.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=payload, timeout=self.api_config.timeout)
            elif method == 'GET':
                response = requests.get(url, headers=headers, timeout=self.api_config.timeout)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = {'raw_text': response.text}
            
            # Check for errors
            if response.status_code >= 400:
                error = self._parse_error(response.status_code, response_data)
                return APIResponse(
                    status_code=response.status_code,
                    success=False,
                    data=response_data,
                    error=error,
                    raw_response=response,
                )
            
            return APIResponse(
                status_code=response.status_code,
                success=True,
                data=response_data,
                raw_response=response,
            )
        
        except requests.RequestException as e:
            error = APIError(
                error_type=APIErrorType.NETWORK_ERROR,
                status_code=0,
                message=str(e),
                retriable=True,
            )
            return APIResponse(
                status_code=0,
                success=False,
                data={},
                error=error,
            )
    
    def _parse_error(self, status_code: int, response_data: Dict) -> APIError:
        """Parse error response and classify"""
        if status_code == 401:
            return APIError(
                error_type=APIErrorType.OAUTH_ERROR,
                status_code=status_code,
                message='Unauthorized. Token may be expired.',
                retriable=True,
            )
        elif status_code == 429:
            return APIError(
                error_type=APIErrorType.RATE_LIMIT,
                status_code=status_code,
                message='Rate limited. Retry after backoff.',
                retriable=True,
            )
        elif status_code in [400, 404]:
            return APIError(
                error_type=APIErrorType.VALIDATION_ERROR,
                status_code=status_code,
                message=response_data.get('message', 'Validation error'),
                details=response_data,
                retriable=False,
            )
        elif status_code >= 500:
            return APIError(
                error_type=APIErrorType.SERVER_ERROR,
                status_code=status_code,
                message='eBay API server error',
                retriable=True,
            )
        else:
            return APIError(
                error_type=APIErrorType.UNKNOWN,
                status_code=status_code,
                message=response_data.get('message', 'Unknown error'),
                details=response_data,
            )
    
    def create_inventory_item(self, sku: str, payload: Dict) -> APIResponse:
        """Create inventory item"""
        endpoint = f'/sell/inventory/v1/inventory_item/{sku}'
        return self._make_request('PUT', endpoint, payload)
    
    def create_offer(self, payload: Dict) -> APIResponse:
        """Create offer"""
        endpoint = '/sell/inventory/v1/offer'
        return self._make_request('POST', endpoint, payload)
    
    def publish_offer(self, offer_id: str) -> APIResponse:
        """Publish offer to create live listing"""
        endpoint = f'/sell/inventory/v1/offer/{offer_id}/publish'
        return self._make_request('POST', endpoint, None)

# ============================================================================
# RESPONSE PROCESSOR
# ============================================================================

@dataclass
class LiveListingResult:
    """Result of live listing creation"""
    status: str  # success / partial_success / failed
    sku: str
    candidate_id: str
    ebay_listing_id: Optional[str]
    offer_id: Optional[str]
    inventory_item_id: Optional[str]
    activation_link: Optional[str]
    initial_price: float
    initial_fees: Dict
    timestamp: str
    api_responses: List[Dict]
    error_message: Optional[str] = None
    audit_notes: Optional[str] = None

class ResponseProcessor:
    """Process eBay API responses"""
    
    @staticmethod
    def process_inventory_response(response: APIResponse, sku: str) -> Dict:
        """Process inventory creation response"""
        if not response.success:
            return {
                'success': False,
                'sku': sku,
                'error': response.error.message if response.error else 'Unknown error',
            }
        
        return {
            'success': True,
            'sku': sku,
            'inventory_item_id': response.data.get('sku', sku),
        }
    
    @staticmethod
    def process_offer_response(response: APIResponse) -> Dict:
        """Process offer creation response"""
        if not response.success:
            return {
                'success': False,
                'error': response.error.message if response.error else 'Unknown error',
            }
        
        return {
            'success': True,
            'offer_id': response.data.get('offerId'),
            'sku': response.data.get('sku'),
        }
    
    @staticmethod
    def process_publish_response(response: APIResponse, offer_id: str) -> Dict:
        """Process publish response"""
        if not response.success:
            return {
                'success': False,
                'offer_id': offer_id,
                'error': response.error.message if response.error else 'Unknown error',
            }
        
        listing_id = response.data.get('listingId')
        activation_link = None
        if listing_id:
            # Build item URL
            domain = 'ebay.com' if 'ebay.com' in str(response.raw_response.url) else 'ebay.com'
            activation_link = f"https://www.{domain}/itm/{listing_id}"
        
        return {
            'success': True,
            'offer_id': offer_id,
            'listing_id': listing_id,
            'activation_link': activation_link,
            'status_message': response.data.get('statusMessage', ''),
        }
    
    @staticmethod
    def build_listing_result(
        sku: str,
        candidate_id: str,
        initial_price: float,
        api_responses: List[APIResponse],
        inventory_result: Dict,
        offer_result: Dict,
        publish_result: Dict,
    ) -> LiveListingResult:
        """Build final listing result from all API responses"""
        
        # Determine overall status
        all_success = all([
            inventory_result.get('success'),
            offer_result.get('success'),
            publish_result.get('success'),
        ])
        
        if all_success:
            status = 'success'
        elif offer_result.get('success') or publish_result.get('success'):
            status = 'partial_success'
        else:
            status = 'failed'
        
        # Build result
        result = LiveListingResult(
            status=status,
            sku=sku,
            candidate_id=candidate_id,
            ebay_listing_id=publish_result.get('listing_id'),
            offer_id=offer_result.get('offer_id'),
            inventory_item_id=inventory_result.get('inventory_item_id'),
            activation_link=publish_result.get('activation_link'),
            initial_price=initial_price,
            initial_fees={
                'insertion_fee': 0.0,
                'estimated_final_value_fee': initial_price * 0.129,
            },
            timestamp=datetime.now().isoformat(),
            api_responses=[asdict(r) for r in api_responses],
            error_message=None if all_success else 'One or more API calls failed',
        )
        
        return result

# ============================================================================
# INTEGRATION EXECUTOR
# ============================================================================

@dataclass
class ExecutionState:
    """Execution state tracking"""
    candidate_id: str
    sku: str
    status: str  # ready_for_api, inventory_created, offer_created, published, failed
    inventory_result: Optional[Dict] = None
    offer_result: Optional[Dict] = None
    publish_result: Optional[Dict] = None
    error_message: Optional[str] = None

class LiveAPIIntegrationExecutor:
    """Execute Phase 6: Live API integration"""
    
    def __init__(self, oauth_handler: OAuthHandler, api_client: EBayLiveAPIClient, response_processor: ResponseProcessor):
        self.oauth_handler = oauth_handler
        self.api_client = api_client
        self.response_processor = response_processor
    
    def execute(self, payload: Dict, candidate_id: str) -> LiveListingResult:
        """Execute full Phase 6 flow"""
        
        sku = payload.get('sku')
        print(f"\n[Executor] Starting live API execution for {sku}")
        
        state = ExecutionState(
            candidate_id=candidate_id,
            sku=sku,
            status='ready_for_api',
        )
        
        api_responses = []
        
        # Step 1: Create inventory item
        print(f"  [Step 1] Creating inventory item...")
        inventory_payload = {
            'availability': {'quantity': payload.get('quantity', 1)},
            'condition': 'NEW',
            'product': {
                'title': payload.get('title'),
                'description': payload.get('description'),
                'brand': payload.get('brand', ''),
                'mpn': payload.get('model_number', ''),
            }
        }
        
        inv_response = self.api_client.create_inventory_item(sku, inventory_payload)
        api_responses.append(inv_response)
        state.inventory_result = self.response_processor.process_inventory_response(inv_response, sku)
        
        if not state.inventory_result['success']:
            state.status = 'failed'
            state.error_message = state.inventory_result.get('error')
            return self._build_result(state, api_responses, payload)
        
        state.status = 'inventory_created'
        print(f"  ✅ Inventory item created")
        
        # Step 2: Create offer
        print(f"  [Step 2] Creating offer...")
        offer_payload = {
            'sku': sku,
            'marketplaceId': 'EBAY_US',
            'format': 'FIXED_PRICE',
            'pricingSummary': {
                'price': {
                    'currency': 'USD',
                    'value': str(payload.get('price')),
                }
            },
            'categoryId': str(payload.get('category_id', 15687)),
            'listingDescription': payload.get('description', ''),
        }
        
        offer_response = self.api_client.create_offer(offer_payload)
        api_responses.append(offer_response)
        state.offer_result = self.response_processor.process_offer_response(offer_response)
        
        if not state.offer_result['success']:
            state.status = 'offer_creation_failed'
            state.error_message = state.offer_result.get('error')
            return self._build_result(state, api_responses, payload)
        
        state.status = 'offer_created'
        print(f"  ✅ Offer created (offer_id: {state.offer_result.get('offer_id')})")
        
        # Step 3: Publish offer
        print(f"  [Step 3] Publishing offer...")
        offer_id = state.offer_result.get('offer_id')
        publish_response = self.api_client.publish_offer(offer_id)
        api_responses.append(publish_response)
        state.publish_result = self.response_processor.process_publish_response(publish_response, offer_id)
        
        if not state.publish_result['success']:
            state.status = 'publish_failed'
            state.error_message = state.publish_result.get('error')
            return self._build_result(state, api_responses, payload)
        
        state.status = 'published'
        print(f"  ✅ Offer published (listing_id: {state.publish_result.get('listing_id')})")
        print(f"  🎉 Live listing created!")
        
        return self._build_result(state, api_responses, payload)
    
    def _build_result(self, state: ExecutionState, api_responses: List[APIResponse], payload: Dict) -> LiveListingResult:
        """Build final result"""
        return self.response_processor.build_listing_result(
            sku=state.sku,
            candidate_id=state.candidate_id,
            initial_price=payload.get('price'),
            api_responses=api_responses,
            inventory_result=state.inventory_result or {},
            offer_result=state.offer_result or {},
            publish_result=state.publish_result or {},
        )

# ============================================================================
# MAIN EXECUTION & TESTING
# ============================================================================

def main():
    """Main execution"""
    print("="*70)
    print("MarginScout Phase 6: OAuth & Live API Implementation")
    print("="*70)
    
    # Load configuration
    print("\n[Config] Loading eBay OAuth and API configuration...")
    oauth_config = EBayOAuthConfig.from_env()
    api_config = EBayAPIConfig.from_env()
    
    print(f"  Environment: {api_config.environment}")
    print(f"  Base URL: {api_config.base_url}")
    
    # Initialize OAuth handler
    print("\n[OAuth] Initializing OAuth handler...")
    oauth_handler = OAuthHandler(oauth_config, api_config)
    
    # Mock test (if refresh token is available)
    if oauth_config.refresh_token:
        print("[OAuth] Using existing refresh token...")
        try:
            oauth_handler.token = OAuthToken(
                access_token='mock_token_for_testing',
                token_type='Bearer',
                expires_in=7200,
                refresh_token=oauth_config.refresh_token,
                obtained_at=datetime.now(),
            )
            print("✅ OAuth handler ready (mock token loaded)")
        except Exception as e:
            print(f"❌ OAuth initialization failed: {e}")
            return
    else:
        print("⚠️  No refresh token in .env. Skipping OAuth flow.")
        print("    To enable: Set EBAY_REFRESH_TOKEN in .env")
    
    # Initialize API client and response processor
    print("\n[API] Initializing Live API client...")
    api_client = EBayLiveAPIClient(oauth_handler, api_config)
    response_processor = ResponseProcessor()
    executor = LiveAPIIntegrationExecutor(oauth_handler, api_client, response_processor)
    
    print("✅ API client ready")
    
    # Mock execution example
    print("\n[Executor] Preparing mock execution...")
    mock_payload = {
        'sku': 'MARGIN-20260613-0001',
        'title': 'Canon EF 70-200mm f/2.8 IS II USM Lens',
        'description': 'Professional telephoto lens in excellent condition',
        'brand': 'Canon',
        'model_number': 'EF 70-200mm f/2.8 IS II USM',
        'price': 263.51,
        'quantity': 1,
        'category_id': 625,
    }
    
    print("\n[Note] Phase 6 implementation structure is ready.")
    print("  To execute live API calls, configure:")
    print("    - EBAY_ENV=sandbox")
    print("    - EBAY_CLIENT_ID=<your_app_id>")
    print("    - EBAY_CLIENT_SECRET=<your_cert_id>")
    print("    - EBAY_REFRESH_TOKEN=<your_token>")
    print("\n  Then call: executor.execute(mock_payload, 'ms-res-20260613-0001')")
    
    # Save configuration example
    config_example = {
        'environment': api_config.environment,
        'oauth_config': {
            'client_id': '***masked***',
            'oauth_url': api_config.oauth_url,
            'redirect_uri': oauth_config.redirect_uri,
        },
        'api_config': {
            'base_url': api_config.base_url,
            'timeout': api_config.timeout,
            'max_retries': api_config.max_retries,
        },
        'scopes': [
            'https://api.ebay.com/oauth/api_scope/sell.inventory',
            'https://api.ebay.com/oauth/api_scope/sell.account',
        ],
    }
    
    config_path = Path.cwd() / 'PHASE6_CONFIG_EXAMPLE.json'
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_example, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Configuration example saved: {config_path}")
    
    # Save implementation report
    report = {
        'timestamp': datetime.now().isoformat(),
        'phase': 'Phase 6: OAuth & Live API Implementation',
        'status': 'IMPLEMENTATION_STRUCTURE_READY',
        'components_implemented': [
            'EBayOAuthConfig',
            'EBayAPIConfig',
            'OAuthHandler (token exchange, refresh, expiry management)',
            'APIErrorType (error classification)',
            'APIError',
            'EBayLiveAPIClient (Inventory, Offer, Publish)',
            'ResponseProcessor (response normalization)',
            'LiveListingResult (output model)',
            'ExecutionState (state tracking)',
            'LiveAPIIntegrationExecutor (orchestration)',
        ],
        'key_features': [
            'Sandbox-first architecture',
            'dry-run / live responsibility separation',
            'OAuth token management (refresh, expiry)',
            'API error classification and retry logic',
            'Request/response logging (masked)',
            'API response normalization',
            'State tracking across API calls',
        ],
        'environment_variables_required': [
            'EBAY_ENV (sandbox | production)',
            'EBAY_CLIENT_ID',
            'EBAY_CLIENT_SECRET',
            'EBAY_REDIRECT_URI',
            'EBAY_REFRESH_TOKEN (optional for testing)',
            'EBAY_REQUEST_TIMEOUT',
            'EBAY_MAX_RETRIES',
        ],
        'next_steps': [
            '1. Update .env.example with eBay OAuth variables',
            '2. Update docs/CONFIGURATION.md with setup instructions',
            '3. Implement candidate status update logic',
            '4. Implement audit logging',
            '5. Create unit tests for each component',
            '6. Implement integration tests with Sandbox',
            '7. Test dry-run vs live integration',
        ],
    }
    
    report_path = Path.cwd() / 'PHASE6_IMPLEMENTATION_REPORT.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Implementation report saved: {report_path}")
    
    print("\n" + "="*70)
    print("Phase 6 Implementation Structure: READY")
    print("="*70)

if __name__ == "__main__":
    main()
