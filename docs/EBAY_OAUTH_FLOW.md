# eBay OAuth 2.0 Flow Specification

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
