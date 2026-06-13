# Phase 6: eBay OAuth & Live API Integration

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
