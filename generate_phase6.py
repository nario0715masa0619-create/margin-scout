#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 6: eBay OAuth & Live API Integration Design
"""

import json
from datetime import datetime
from pathlib import Path

def create_phase6_design_doc():
    """Create docs/PHASE6_EBAY_API_INTEGRATION.md"""
    content = r'''# Phase 6: eBay OAuth & Live API Integration

**Date:** 2026-06-13  
**Status:** Design Phase  
**Target:** Live eBay API integration, OAuth authentication, real listing creation

## Overview

Phase 6 implements the final layer of MarginScout: **live eBay API integration**. It takes execution-ready payloads from Phase 5 and submits them to eBay's actual API to create listings, retrieve real listing IDs, and update candidate status.

### Key Responsibilities

1. **OAuth 2.0 Authentication** – Obtain and manage eBay API access tokens
2. **Live API Client** – Call eBay Sell API endpoints (create inventory item, create listing)
3. **Error Handling** – Handle eBay API errors, rate limiting, retries
4. **Response Processing** – Extract real_listing_id, activation_link, fee data
5. **Status Update** – Change candidate status from research → listed
6. **Audit Logging** – Record successful listings with timestamp, eBay listing_id, activation link

---

## OAuth 2.0 Authentication Flow

### Pre-requisites

- eBay Developer Account (https://developer.ebay.com)
- App ID (Client ID)
- Cert ID (Client Secret)
- Auth/Refresh Token (obtained from OAuth flow or stored)

### Flow Diagram

```
[User]
   ↓
[OAuth Handler: Request authorization]
   ↓
[eBay OAuth Endpoint: User grants permission]
   ↓
[eBay returns Authorization Code]
   ↓
[OAuth Handler: Exchange code for access_token + refresh_token]
   ↓
[Store tokens in secure config / .env]
   ↓
[API Client: Use access_token for API calls]
   ↓
[If token expires: Refresh using refresh_token]
```

### Implementation Details

**Step 1: Get Authorization Code**
```
GET https://auth.ebay.com/oauth2/authorize?
    client_id={CLIENT_ID}&
    response_type=code&
    redirect_uri={REDIRECT_URI}&
    scope=https://api.ebay.com/oauth/api_scope/sell.inventory ...
```

**Step 2: Exchange Code for Token**
```
POST https://api.ebay.com/identity/v1/oauth2/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code={AUTH_CODE}&
redirect_uri={REDIRECT_URI}&
client_id={CLIENT_ID}&
client_secret={CLIENT_SECRET}
```

**Response:**
```json
{
  "access_token": "v^1.1#i^1#p^3#f^0#I^3#r^0#...",
  "token_type": "Bearer",
  "expires_in": 7200,
  "refresh_token": "v^1.1#i^1#f^0#p^3#...",
  "refresh_token_expires_in": 47304000
}
```

**Step 3: Use Access Token for API Calls**
```
GET https://api.ebay.com/sell/inventory/v1/inventory_item
Authorization: Bearer {ACCESS_TOKEN}
```

---

## Live API Endpoints

### 1. Create Inventory Item
**Endpoint:** POST `/sell/inventory/v1/inventory_item/{sku}`

**Request:**
```json
{
  "availability": {
    "quantity": 1
  },
  "condition": "NEW",
  "product": {
    "title": "Canon EF 70-200mm f/2.8 IS II USM Lens",
    "description": "Professional telephoto lens...",
    "brand": "Canon",
    "mpn": "EF 70-200mm f/2.8 IS II USM"
  }
}
```

**Response:**
```json
{
  "sku": "MARGIN-20260613-0001",
  "status": 201  // Created
}
```

### 2. Publish Listing
**Endpoint:** POST `/sell/inventory/v1/offer`

**Request:**
```json
{
  "sku": "MARGIN-20260613-0001",
  "marketplaceId": "EBAY_US",
  "format": "FIXED_PRICE",
  "pricingSummary": {
    "price": {
      "currency": "USD",
      "value": "138.69"
    }
  },
  "categoryId": "625",
  "listingDescription": "Professional telephoto lens...",
  "listingPolicies": {
    "paymentPolicyId": "...",
    "returnPolicyId": "...",
    "fulfillmentPolicyId": "..."
  }
}
```

**Response:**
```json
{
  "offerId": "9876543210",
  "listingId": "386547829380",
  "status": 201
}
```

### 3. Publish Offer to Create Live Listing
**Endpoint:** POST `/sell/inventory/v1/offer/{offerId}/publish`

**Response:**
```json
{
  "listingId": "386547829380",
  "status": 200,
  "statusMessage": "Offer published successfully"
}
```

---

## Error Handling Strategy

### Error Categories

**Authentication Errors**
- Invalid credentials
- Token expired (retry with refresh_token)
- Insufficient permissions

**Validation Errors**
- Missing required fields
- Invalid category_id
- Price out of bounds
- Title too long

**Rate Limiting (429)**
- Retry with exponential backoff
- Implement request queue

**Server Errors (5xx)**
- Retry with backoff
- Log for manual review

### Retry Logic
- Max retries: 3
- Backoff: exponential (1s, 2s, 4s)
- Trigger: 429, 500, 502, 503 (transient errors only)
- No retry: 400, 401, 403, 404 (hard errors)

### Data Model: LiveListingResult
```python
@dataclass
class LiveListingResult:
    """Result of live listing creation"""
    status: str  # success / partial / failed
    sku: str
    candidate_id: str
    ebay_listing_id: Optional[str]
    offer_id: Optional[str]
    activation_link: Optional[str]
    initial_price: float
    initial_fees: Dict
    timestamp: str
    error_message: Optional[str]
    api_response: Dict
    audit_notes: Optional[str]
```

---

## Status Update Flow

After successful listing creation:

**Update Candidate Status**
- research → listed
- Add ebay_listing_id, activation_link
- Set listed_at timestamp

**Record Audit Log**
- Log listing ID, price, fees, activation link
- Log API response for traceability

**Return to User**
- Provide activation link (user clicks to view live listing)
- Display fees and next steps

---

## Implementation Plan

### Phase 6 Modules

**oauth_handler.py**
- `OAuthHandler` class
- Methods: `request_authorization()`, `exchange_code_for_token()`, `refresh_token()`, `is_token_valid()`

**ebay_api_client_live.py**
- `EBayLiveAPIClient` class
- Methods: `create_inventory_item()`, `create_offer()`, `publish_offer()`, `handle_error()`

**response_processor.py**
- `ResponseProcessor` class
- Methods: `process_inventory_response()`, `process_offer_response()`, `process_publish_response()`, `build_listing_result()`

**api_integration_executor.py**
- `APIIntegrationExecutor` class
- Methods: `execute()` (orchestrate OAuth, API calls, status update)

### Integration Test
```
Phase 5 ExecutionReadyPayload
  ↓
[API Integration Executor]
  ↓
OAuth token acquired
  ↓
Create inventory item (API call)
  ↓
Create offer (API call)
  ↓
Publish offer (API call)
  ↓
LiveListingResult with real listing_id and activation_link
  ↓
Update candidate status to listed
```

### Preconditions
- OAuth credentials configured in .env or secure config
- Phase 5 execution completed (ready_for_phase_6)
- eBay Sandbox account (for testing) and Production account (for live)

### Next Steps (Phase 7+)
- Phase 7: Inventory Sync & Order Management
- Phase 8: Seller Feedback & Analytics
- Phase 9: Automated Repricing & Monitoring

## Summary
Phase 6 is the live integration layer that bridges MarginScout's research, CSV, and payload preparation logic to eBay's actual marketplace. Upon successful Phase 6 completion, items move from draft state to live listing on eBay, available for purchase by real customers.
'''
    return content

def create_oauth_flow_doc():
    """Create docs/EBAY_OAUTH_FLOW.md"""
    content = r'''# eBay OAuth 2.0 Flow Specification

Date: 2026-06-13

## Overview
eBay OAuth 2.0 enables MarginScout to authenticate users and obtain access tokens for API calls without storing passwords.

## Configuration
Required in `.env` or secure config:
```
EBAY_CLIENT_ID=your_app_id
EBAY_CLIENT_SECRET=your_cert_id
EBAY_REDIRECT_URI=http://localhost:8080/callback
EBAY_OAUTH_ENDPOINT=https://auth.ebay.com/oauth2/authorize
EBAY_TOKEN_ENDPOINT=https://api.ebay.com/identity/v1/oauth2/token
EBAY_API_ENDPOINT=https://api.ebay.com
```

## Token Management
- Access Token Lifetime: 7200 seconds (2 hours)
- Refresh Token Lifetime: 47304000 seconds (~18 months)
- Token Refresh: Before expiration or on 401 response

## Scope
Required scopes:
- https://api.ebay.com/oauth/api_scope/sell.inventory
- https://api.ebay.com/oauth/api_scope/sell.account

## Flow Diagram
```
User launches MarginScout
        ↓
[Check if token exists and valid]
        ↓
No → Redirect to eBay OAuth endpoint
        ↓
[User grants permission on eBay]
        ↓
eBay redirects to callback with authorization code
        ↓
[Exchange code for tokens]
        ↓
[Store tokens in secure config]
        ↓
[Ready for API calls]
```
'''
    return content

def create_live_api_spec_doc():
    """Create docs/EBAY_LIVE_API_SPEC.md"""
    content = r'''# eBay Live API Specification

Date: 2026-06-13

## Endpoints Used

### 1. Create Inventory Item
- Method: PUT
- Endpoint: `/sell/inventory/v1/inventory_item/{sku}`
- Purpose: Create a draft inventory item

### 2. Create Offer
- Method: POST
- Endpoint: `/sell/inventory/v1/offer`
- Purpose: Create a draft offer (pricing, policies)

### 3. Publish Offer
- Method: POST
- Endpoint: `/sell/inventory/v1/offer/{offerId}/publish`
- Purpose: Publish offer to create live listing

## Request/Response Examples
See `examples/ebay_live_api_response_sample.json`

## Error Response Format
```json
{
  "errors": [
    {
      "errorId": 25001,
      "domain": "API_INVENTORY",
      "category": "REQUEST",
      "message": "Invalid SKU",
      "longMessage": "The SKU provided is invalid or already exists"
    }
  ]
}
```

## Rate Limiting
- Calls per Minute: 60 (typical)
- Header: `X-RateLimit-Remaining`
- Action: Implement backoff when limit approached
'''
    return content

def create_oauth_sample():
    """Create examples/ebay_oauth_request_sample.json"""
    sample = {
        "oauth_flow_steps": [
            {
                "step": 1,
                "name": "Request Authorization",
                "method": "GET",
                "url": "https://auth.ebay.com/oauth2/authorize",
                "parameters": {
                    "client_id": "YOUR_APP_ID",
                    "response_type": "code",
                    "redirect_uri": "http://localhost:8080/callback",
                    "scope": "https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account"
                },
                "result": "User is redirected to eBay login page"
            },
            {
                "step": 2,
                "name": "User Grants Permission",
                "result": "eBay redirects to redirect_uri with authorization code in query string"
            },
            {
                "step": 3,
                "name": "Exchange Code for Token",
                "method": "POST",
                "url": "https://api.ebay.com/identity/v1/oauth2/token",
                "headers": {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": "Basic BASE64(CLIENT_ID:CLIENT_SECRET)"
                },
                "body": {
                    "grant_type": "authorization_code",
                    "code": "AUTHORIZATION_CODE_FROM_STEP_2",
                    "redirect_uri": "http://localhost:8080/callback"
                },
                "response": {
                    "access_token": "v1.1#i1#p3#f0#...",
                    "token_type": "Bearer",
                    "expires_in": 7200,
                    "refresh_token": "v1.1#i1#f0#p3#..."
                }
            }
        ]
    }
    return json.dumps(sample, indent=2, ensure_ascii=False)

def create_live_api_response_sample():
    """Create examples/ebay_live_api_response_sample.json"""
    sample = {
        "successful_flow": {
            "step_1_create_inventory_item": {
                "status": 201,
                "response": {
                    "sku": "MARGIN-20260613-0001"
                }
            },
            "step_2_create_offer": {
                "status": 201,
                "response": {
                    "offerId": "9876543210",
                    "sku": "MARGIN-20260613-0001"
                }
            },
            "step_3_publish_offer": {
                "status": 200,
                "response": {
                    "listingId": "386547829380",
                    "statusMessage": "Offer published successfully",
                    "link": "https://www.ebay.com/itm/386547829380"
                }
            },
            "final_result": {
                "ebay_listing_id": "386547829380",
                "activation_link": "https://www.ebay.com/itm/386547829380",
                "sku": "MARGIN-20260613-0001",
                "initial_price": 263.51,
                "initial_fees": {
                    "insertion_fee": 0.0,
                    "final_value_fee": 33.99
                },
                "status": "success"
            }
        },
        "error_examples": {
            "invalid_sku": {
                "status": 400,
                "errors": [
                    {
                        "errorId": 25001,
                        "domain": "API_INVENTORY",
                        "category": "REQUEST",
                        "message": "Invalid SKU",
                        "longMessage": "The SKU is invalid or already in use"
                    }
                ]
            },
            "rate_limited": {
                "status": 429,
                "headers": {
                    "Retry-After": "60",
                    "X-RateLimit-Remaining": "0"
                }
            },
            "unauthorized": {
                "status": 401,
                "errors": [
                    {
                        "errorId": 1001,
                        "domain": "API_AUTH",
                        "category": "REQUEST",
                        "message": "Invalid access token"
                    }
                ]
            }
        }
    }
    return json.dumps(sample, indent=2, ensure_ascii=False)

def create_skeleton_code(project_dir):
    """Create src/api_integration/ skeleton code"""
    api_dir = Path(project_dir) / "src" / "api_integration"
    api_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py
    with open(api_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write('''"""
MarginScout Phase 6: eBay API Integration Module
Handles OAuth authentication and live API calls.
"""

from .oauth_handler import OAuthHandler
from .ebay_api_client_live import EBayLiveAPIClient
from .response_processor import ResponseProcessor
from .api_integration_executor import APIIntegrationExecutor

__all__ = [
    "OAuthHandler",
    "EBayLiveAPIClient",
    "ResponseProcessor",
    "APIIntegrationExecutor",
]
''')

    # oauth_handler.py
    with open(api_dir / "oauth_handler.py", "w", encoding="utf-8") as f:
        f.write('''"""
OAuth 2.0 Handler for eBay authentication.
"""

from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime, timedelta
import os

@dataclass
class OAuthToken:
    """OAuth token data"""
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str]
    obtained_at: str

class OAuthHandler:
    """Handle eBay OAuth 2.0 authentication"""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize OAuth handler.
        
        Args:
            client_id: eBay App ID
            client_secret: eBay Cert ID
            redirect_uri: OAuth redirect URI (e.g., http://localhost:8080/callback)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.oauth_endpoint = "https://auth.ebay.com/oauth2/authorize"
        self.token_endpoint = "https://api.ebay.com/identity/v1/oauth2/token"
        self.current_token: Optional[OAuthToken] = None

    def request_authorization(self) -> str:
        """
        Generate authorization URL for user to visit.
        """
        raise NotImplementedError("Authorization URL generation not yet implemented")

    def exchange_code_for_token(self, auth_code: str) -> OAuthToken:
        """
        Exchange authorization code for access token.
        """
        raise NotImplementedError("Token exchange not yet implemented")

    def refresh_token(self) -> OAuthToken:
        """
        Refresh access token using refresh token.
        """
        raise NotImplementedError("Token refresh not yet implemented")

    def is_token_valid(self) -> bool:
        """
        Check if current token is valid.
        """
        raise NotImplementedError("Token validation not yet implemented")

    def get_access_token(self) -> str:
        """
        Get valid access token (refresh if needed).
        """
        raise NotImplementedError("Access token retrieval not yet implemented")
''')

    # ebay_api_client_live.py
    with open(api_dir / "ebay_api_client_live.py", "w", encoding="utf-8") as f:
        f.write('''"""
eBay Live API Client
Handles actual API calls to eBay endpoints.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import requests

@dataclass
class APIResponse:
    """API response wrapper"""
    status_code: int
    data: Dict
    errors: list
    headers: Dict

class EBayLiveAPIClient:
    """eBay API client for live calls"""

    def __init__(self, oauth_handler):
        """
        Initialize API client.
        
        Args:
            oauth_handler: OAuthHandler instance with valid token
        """
        self.oauth_handler = oauth_handler
        self.base_url = "https://api.ebay.com"
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def create_inventory_item(self, sku: str, payload: Dict) -> APIResponse:
        """
        Create inventory item on eBay.
        """
        raise NotImplementedError("Create inventory item not yet implemented")

    def create_offer(self, payload: Dict) -> APIResponse:
        """
        Create offer (pricing and policies).
        """
        raise NotImplementedError("Create offer not yet implemented")

    def publish_offer(self, offer_id: str) -> APIResponse:
        """
        Publish offer to create live listing.
        """
        raise NotImplementedError("Publish offer not yet implemented")

    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> APIResponse:
        """
        Make HTTP request to eBay API.
        """
        raise NotImplementedError("HTTP request not yet implemented")
''')

    # response_processor.py
    with open(api_dir / "response_processor.py", "w", encoding="utf-8") as f:
        f.write('''"""
Response processor for eBay API responses.
"""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class LiveListingResult:
    """Result of live listing creation"""
    status: str  # success / partial / failed
    sku: str
    candidate_id: str
    ebay_listing_id: Optional[str]
    offer_id: Optional[str]
    activation_link: Optional[str]
    initial_price: float
    initial_fees: Dict
    timestamp: str
    error_message: Optional[str]
    api_response: Dict

class ResponseProcessor:
    """Process eBay API responses"""

    @staticmethod
    def process_inventory_response(response_dict: Dict) -> Dict:
        """
        Process create inventory item response.
        """
        raise NotImplementedError("Inventory response processing not yet implemented")

    @staticmethod
    def process_offer_response(response_dict: Dict) -> Dict:
        """
        Process create offer response.
        """
        raise NotImplementedError("Offer response processing not yet implemented")

    @staticmethod
    def process_publish_response(response_dict: Dict) -> Dict:
        """
        Process publish offer response.
        """
        raise NotImplementedError("Publish response processing not yet implemented")

    @staticmethod
    def build_listing_result(
        status: str,
        sku: str,
        candidate_id: str,
        ebay_listing_id: Optional[str],
        activation_link: Optional[str],
        initial_price: float,
        initial_fees: Dict,
        api_response: Dict,
        error_message: Optional[str] = None
    ) -> LiveListingResult:
        """
        Build final listing result.
        """
        raise NotImplementedError("Listing result building not yet implemented")
''')

    # api_integration_executor.py
    with open(api_dir / "api_integration_executor.py", "w", encoding="utf-8") as f:
        f.write('''"""
Main executor for Phase 6 API integration.
Orchestrates OAuth, API calls, and status updates.
"""

from typing import Dict, Optional

class APIIntegrationExecutor:
    """Execute Phase 6: API integration"""

    def __init__(self, oauth_handler, api_client, response_processor):
        """
        Initialize executor.
        
        Args:
            oauth_handler: OAuthHandler instance
            api_client: EBayLiveAPIClient instance
            response_processor: ResponseProcessor instance
        """
        self.oauth_handler = oauth_handler
        self.api_client = api_client
        self.response_processor = response_processor

    def execute(self, execution_ready_payload: Dict) -> Dict:
        """
        Execute full Phase 6 flow: OAuth → API calls → status update.
        """
        raise NotImplementedError("API integration execution not yet implemented")

    def _create_inventory_item(self, payload: Dict) -> Dict:
        """Create inventory item and handle errors"""
        raise NotImplementedError()

    def _create_offer(self, sku: str, price: float, category_id: int) -> Dict:
        """Create offer and handle errors"""
        raise NotImplementedError()

    def _publish_offer(self, offer_id: str) -> Dict:
        """Publish offer and handle errors"""
        raise NotImplementedError()

    def _update_candidate_status(self, candidate_id: str, ebay_listing_id: str, activation_link: str) -> None:
        """Update candidate status from research to listed"""
        raise NotImplementedError()
''')

def create_phase6_completion_report(project_dir):
    """Create PHASE6_COMPLETION_REPORT.json"""
    report = {
        "project_name": "MarginScout",
        "phase": "Phase 6: eBay OAuth & Live API Integration Design",
        "status": "COMPLETED",
        "timestamp": datetime.now().isoformat(),
        "documents_created": [
            "docs/PHASE6_EBAY_API_INTEGRATION.md",
            "docs/EBAY_OAUTH_FLOW.md",
            "docs/EBAY_LIVE_API_SPEC.md",
        ],
        "examples_created": [
            "examples/ebay_oauth_request_sample.json",
            "examples/ebay_live_api_response_sample.json",
        ],
        "skeleton_code_created": [
            "src/api_integration/__init__.py",
            "src/api_integration/oauth_handler.py",
            "src/api_integration/ebay_api_client_live.py",
            "src/api_integration/response_processor.py",
            "src/api_integration/api_integration_executor.py",
        ],
        "key_findings": {
            "oauth_flow": "3-step flow: authorization → exchange code for token → use access_token for API calls",
            "oauth_token_lifetime": "Access token: 7200s (2h), Refresh token: 47304000s (~18mo)",
            "api_endpoints": [
                "/sell/inventory/v1/inventory_item/{sku} (PUT)",
                "/sell/inventory/v1/offer (POST)",
                "/sell/inventory/v1/offer/{offerId}/publish (POST)"
            ],
            "error_handling": "Retry on 429/5xx, no retry on 400/401/403/404",
            "rate_limiting": "60 calls/minute typical, check X-RateLimit-Remaining header",
            "final_output": "LiveListingResult with ebay_listing_id, activation_link, initial_fees"
        },
        "design_principles": [
            "OAuth tokens stored securely in .env or config",
            "Token refresh automated on expiration",
            "All API errors categorized and logged",
            "Rate limiting respected with backoff strategy",
            "Candidate status updated to 'listed' on success",
            "Activation link returned to user"
        ],
        "next_phase": "Phase 7: Inventory Sync & Order Management (track sold items, update inventory, handle returns)",
        "implementation_notes": [
            "OAuth handler: implement token exchange and refresh logic",
            "API client: implement HTTP requests with error handling",
            "Response processor: extract listing_id and activation_link from API response",
            "Executor: orchestrate full flow with proper error handling",
            "Test with eBay Sandbox first, then Production"
        ],
        "files_modified": [
            "README.md (Phase 6 status section to be added)"
        ]
    }
    
    report_path = Path(project_dir) / "PHASE6_COMPLETION_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report_path


def update_readme(project_dir):
    """Update README.md with Phase 6 status"""
    readme_path = Path(project_dir) / "README.md"
    
    phase6_section = """
---

## 📋 Phase 6: eBay OAuth & Live API Integration Design
**Status**: ✅ Completed
**Date**: 2026-06-13

### Deliverables
- docs/PHASE6_EBAY_API_INTEGRATION.md – Overall design, OAuth flow, API endpoints, error handling
- docs/EBAY_OAUTH_FLOW.md – OAuth 2.0 authentication flow specification
- docs/EBAY_LIVE_API_SPEC.md – Live eBay API endpoints and response formats
- examples/ebay_oauth_request_sample.json – OAuth request examples
- examples/ebay_live_api_response_sample.json – API response examples (success & errors)
- src/api_integration/ – Skeleton code (OAuthHandler, API client, response processor)

### Key Design Decisions
- OAuth Flow: 3-step (authorization → exchange code → use token)
- Token Lifetime: Access token 2 hours, refresh token ~18 months
- API Endpoints: Inventory item (PUT), Offer creation (POST), Offer publish (POST)
- Error Handling: Categorized retry logic (3 retries with exponential backoff)
- Rate Limiting: 60 calls/min, implement backoff on 429 response
- Final Output: LiveListingResult with real eBay listing ID and activation link

### Integration Flow
```
Phase 5 ExecutionReadyPayload
  ↓
[OAuth Token Validation]
  ↓
[Create Inventory Item (API)]
  ↓
[Create Offer (API)]
  ↓
[Publish Offer → Live Listing (API)]
  ↓
LiveListingResult with ebay_listing_id + activation_link
  ↓
[Update Candidate Status: research → listed]
```

### Next Phase
Phase 7: Inventory Sync & Order Management (track sold items, handle returns, update inventory)
"""
    
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "Phase 6:" not in content:
            with open(readme_path, "a", encoding="utf-8") as f:
                f.write(phase6_section)
    else:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(phase6_section)


def main():
    """Generate all Phase 6 artifacts"""
    project_dir = Path.cwd()
    
    print("Creating Phase 6 design documents...")
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    print("✓ docs/PHASE6_EBAY_API_INTEGRATION.md")
    with open(docs_dir / "PHASE6_EBAY_API_INTEGRATION.md", "w", encoding="utf-8") as f:
        f.write(create_phase6_design_doc())
        
    print("✓ docs/EBAY_OAUTH_FLOW.md")
    with open(docs_dir / "EBAY_OAUTH_FLOW.md", "w", encoding="utf-8") as f:
        f.write(create_oauth_flow_doc())
        
    print("✓ docs/EBAY_LIVE_API_SPEC.md")
    with open(docs_dir / "EBAY_LIVE_API_SPEC.md", "w", encoding="utf-8") as f:
        f.write(create_live_api_spec_doc())
        
    print("\nCreating examples...")
    examples_dir = project_dir / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    print("✓ examples/ebay_oauth_request_sample.json")
    with open(examples_dir / "ebay_oauth_request_sample.json", "w", encoding="utf-8") as f:
        f.write(create_oauth_sample())
        
    print("✓ examples/ebay_live_api_response_sample.json")
    with open(examples_dir / "ebay_live_api_response_sample.json", "w", encoding="utf-8") as f:
        f.write(create_live_api_response_sample())
        
    print("\nCreating skeleton code...")
    create_skeleton_code(project_dir)
    print("✓ src/api_integration/ (5 files)")
    
    print("\nCreating completion report...")
    create_phase6_completion_report(project_dir)
    print("✓ PHASE6_COMPLETION_REPORT.json")
    
    print("\nUpdating README...")
    update_readme(project_dir)
    print("✓ README.md")
    
    print("\n" + "="*70)
    print("Phase 6: eBay OAuth & Live API Integration Design COMPLETED")
    print("="*70)
    print("\nGenerated files:")
    print("  Docs: 3 files")
    print("  Examples: 2 files")
    print("  Skeleton code: 5 files")
    print("  Report: 1 file")
    print("  Total: 11 files created/updated")
    print("\nNext steps:")
    print("  1. Review docs/PHASE6_EBAY_API_INTEGRATION.md")
    print("  2. Configure .env with EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_REDIRECT_URI")
    print("  3. Implement src/api_integration/ modules")
    print("  4. Test with eBay Sandbox environment")
    print("  5. Proceed to Phase 7: Inventory Sync & Order Management")

if __name__ == "__main__":
    main()
