# MarginScout Configuration Guide

## Overview

MarginScout uses environment variables for all configuration. See `.env.example` for defaults.

## Phase 1-5: Internal Configuration

Standard settings for CSV processing, listing generation, and dry-run:

```
RESEARCH_MODE=research_and_csv_export
CSV_INPUT_DIR=examples
CSV_OUTPUT_DIR=data/csv_output
LISTING_STATUS_LOG=data/listing_status.log
```

## Phase 6: eBay OAuth & Live API Setup

### Step 1: Create eBay Developer Account

Visit https://developer.ebay.com and:
1. Sign in / Create account
2. Create Application (Keyset)
3. Generate Client ID and Cert ID
4. Set Redirect URI (default: http://localhost:8080/callback)

### Step 2: Environment Variables

Copy `.env.example` to `.env` and fill in OAuth credentials:

```bash
# OAuth Credentials
EBAY_CLIENT_ID=<your_app_id>
EBAY_CLIENT_SECRET=<your_cert_id>
EBAY_REDIRECT_URI=http://localhost:8080/callback

# Token Management
EBAY_REFRESH_TOKEN=<obtained_from_oauth_flow>

# Environment
EBAY_ENV=sandbox  # Use 'sandbox' for testing, 'production' for live

# API Settings
EBAY_REQUEST_TIMEOUT=30
EBAY_MAX_RETRIES=3
EBAY_RETRY_BACKOFF_FACTOR=2.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=data/margin_scout.log
AUDIT_LOG_FILE=data/audit_trail.log
```

### Step 3: Get OAuth Refresh Token

Run OAuth flow to obtain tokens:

```python
from src.api_integration.oauth_handler import OAuthHandler, EBayOAuthConfig, EBayAPIConfig

config = EBayOAuthConfig.from_env()
api_config = EBayAPIConfig.from_env()
handler = OAuthHandler(config, api_config)

# Get authorization URL
auth_url = handler.get_authorization_url([
    'https://api.ebay.com/oauth/api_scope/sell.inventory',
    'https://api.ebay.com/oauth/api_scope/sell.account',
])

print(f"Visit: {auth_url}")
# User grants permission, gets authorization code in redirect_uri

# Exchange code for token
token = handler.exchange_code_for_token(auth_code)
print(f"Refresh token: {token.refresh_token}")
# Save to .env as EBAY_REFRESH_TOKEN
```

### Step 4: Sandbox vs Production

MarginScout uses **Sandbox-first** approach:

- **Sandbox:** Testing, development, safe experimentation
- **Production:** Live listings (only after Sandbox validation)

Set via `.env`:

```
EBAY_ENV=sandbox    # For testing
EBAY_ENV=production # For live (use with caution!)
```

### Step 5: Security Best Practices

1. ✅ Never commit `.env` to Git (configured in `.gitignore`)
2. ✅ Use environment variables for all secrets
3. ✅ Log level set to INFO (not DEBUG) in production
4. ✅ Check `.env` permissions (chmod 600 on Unix)
5. ✅ Rotate refresh tokens periodically

## Troubleshooting

### Issue: EBAY_REFRESH_TOKEN not found
**Solution:** Run OAuth flow to get token, save to `.env`

### Issue: 401 Unauthorized
**Solution:** Token may be expired. Token refresh is automatic, but check `.env` EBAY_REFRESH_TOKEN value

### Issue: 429 Rate Limit
**Solution:** Wait and retry. Backoff implemented automatically in API client.

### Issue: 400 Validation Error
**Solution:** Check payload format (title length ≤ 80, price range, valid category ID)

## Verification

To verify configuration:

```bash
# Test OAuth config loads
python -c "from src.api_integration.oauth_handler import EBayOAuthConfig; print('✓ Config loads')"

# Test API client initializes
python -c "from src.api_integration.api_client_live import EBayLiveAPIClient; print('✓ API client loads')"

# Run Phase 3-5 dry-run (should be unchanged)
python implement_phases_3_5_fixed.py
```

## Environment Variables Reference

| Variable | Type | Example | Required |
|----------|------|---------|----------|
| EBAY_ENV | string | sandbox \| production | Yes |
| EBAY_CLIENT_ID | string | AppId_123456 | Yes |
| EBAY_CLIENT_SECRET | string | CertId_abcdef | Yes |
| EBAY_REDIRECT_URI | string | http://localhost:8080/callback | Yes |
| EBAY_REFRESH_TOKEN | string | v^1.1#i^1#... | For live only |
| EBAY_REQUEST_TIMEOUT | int | 30 | No (default: 30) |
| EBAY_MAX_RETRIES | int | 3 | No (default: 3) |
| LOG_LEVEL | string | INFO \| DEBUG | No (default: INFO) |
