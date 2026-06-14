# MarginScout Sandbox Test Execution Guide

## Overview
This guide provides instructions on how to run the eBay Sandbox connection test (Phase 6). The test verifies that OAuth authentication, Inventory API, Offer API, and Publish API function correctly without affecting production data.

## Prerequisites

### 1. eBay Developer Account
Ensure you have an eBay developer account and have generated **Sandbox** keys (App ID / Client ID, Cert ID / Client Secret).

### 2. Configure `.env`
Ensure your `.env` file is properly configured. It should be located at `C:\NewProjects\margin-scout\.env` or `C:\Users\{Username}\.marginscount\.env`.

```bash
# MUST be set to sandbox
EBAY_ENV=sandbox

# Your Sandbox Keys
EBAY_CLIENT_ID=your_sandbox_app_id
EBAY_CLIENT_SECRET=your_sandbox_cert_id
EBAY_REDIRECT_URI=http://localhost:8080/callback

# Get this from your eBay dev portal (OAuth tool for Sandbox)
EBAY_REFRESH_TOKEN=your_sandbox_refresh_token
```

> **Note:** If you don't have a refresh token, run the test script once. It will output an authorization URL. You will need to visit that URL, grant access to your sandbox account, and exchange the resulting code for a refresh token.

## Running the Test

Open your terminal or PowerShell and run:

```bash
cd C:\NewProjects\margin-scout
# Ensure your Python environment is active if using a virtualenv
python sandbox_connection_test.py
```

## Success vs Failure

### What Success Looks Like
You should see output similar to:
```
[INFO] Initializing OAuth Configuration (Sandbox)...
[INFO] OAuth connection SUCCESS. Token: v^1.1#i...
[INFO] Starting E2E Sandbox Test for SKU: MARGIN-SANDBOX-20260613123456
[INFO] Creating inventory item for SKU: MARGIN-SANDBOX-20260613123456
[INFO] Creating offer for SKU: MARGIN-SANDBOX-20260613123456
[INFO] Publishing offer 123456789 for SKU: MARGIN-SANDBOX-20260613123456
[INFO] ================================================================
[INFO] TEST COMPLETED. Status: SUCCESS
[INFO] Listing ID: 110000000001
[INFO] Activation Link: https://www.sandbox.ebay.com/itm/110000000001
[INFO] Detailed result saved to PHASE6_SANDBOX_TEST_RESULT.json
```

### Common Failures & Fixes
- **OAuth fails (401 Unauthorized):** Your Client ID, Client Secret, or Refresh Token is invalid or expired. Double-check your eBay Developer Portal.
- **Inventory/Offer fails (400 Bad Request):** The sandbox dummy payload may be missing required fields for your specific sandbox account (e.g., location keys or return policies). Check `PHASE6_SANDBOX_TEST_RESULT.json` for the exact `errorId` and `message`.
- **EBAY_ENV error:** Ensure `EBAY_ENV=sandbox` in your `.env`.

## Post-Test Actions
After running the test, take the output and use it to fill in `SANDBOX_CONNECTION_TEST_REPORT.md` to formally document the success or identify necessary adjustments.
