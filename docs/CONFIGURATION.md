# MarginScout Environment Configuration Guide

## Overview

MarginScout stores environment configuration (API keys, secrets, etc.) outside the project repository for security reasons.

Configuration files are stored in the user's home directory:
- **Location**: `C:\Users\{ユーザ名}\.marginscount\.env`
- **Access**: Local user only
- **Version Control**: NOT tracked in Git (security)

---

## Setup Instructions

### 1. Configuration Directory

The configuration directory is automatically created at:
```
C:\Users\nario\.marginscount\
```

### 2. Environment File

Create or edit the `.env` file:
```
C:\Users\nario\.marginscount\.env
```

### 3. Required Configuration

**eBay API Keys (Minimum):**
```
EBAY_SANDBOX_CLIENT_ID=<your_sandbox_client_id>
EBAY_SANDBOX_CLIENT_SECRET=<your_sandbox_client_secret>
EBAY_APP_ID=<your_app_id>
```

### 4. Loading Configuration

The application loads configuration in this order:

1. **User home directory** (highest priority)
   ```
   C:\Users\{ユーザ名}\.marginscount\.env
   ```

2. **Project directory** (optional, if exists)
   ```
   .env (NOT recommended - for development only)
   ```

3. **Environment variables** (system level)

4. **Default values** (application defaults)

---

## Security Best Practices

### ✅ DO

- ✓ Store `.env` in user home directory
- ✓ Restrict file permissions: `icacls C:\Users\{ユーザ名}\.marginscount /grant:r %USERNAME%:F /inheritance:r`
- ✓ Use strong, unique API keys
- ✓ Rotate keys periodically
- ✓ Use sandbox credentials for development
- ✓ Use production credentials only for live operations
- ✓ Keep `.env` out of version control

### ❌ DON'T

- ✗ Commit `.env` to Git
- ✗ Share `.env` files via email or chat
- ✗ Store passwords in plain text elsewhere
- ✗ Use same keys across multiple environments
- ✗ Leave `.env` readable by other users
- ✗ Push production keys to development branches

---

## Configuration File Structure

```
C:\Users\{ユーザ名}\
├── .marginscount/                  ← Configuration directory
│   ├── .env                        ← Main configuration (do not commit)
│   ├── .env.example                ← Template (can commit)
│   └── config.local.json           ← Local overrides (optional, do not commit)
├── AppData/
├── Desktop/
└── Documents/
```

---

## Environment Variables Reference

### eBay API

| Variable | Type | Required | Example |
|----------|------|----------|---------|
| EBAY_SANDBOX_CLIENT_ID | string | Yes (dev) | abc123xyz |
| EBAY_SANDBOX_CLIENT_SECRET | string | Yes (dev) | secret456 |
| EBAY_APP_ID | string | Yes | myapp |
| EBAY_CERT_ID | string | Optional | cert789 |
| EBAY_DEV_ID | string | Optional | devid000 |

### Application

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| APP_ENV | string | development | Environment (development, staging, production) |
| LOG_LEVEL | string | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| DEBUG_MODE | boolean | false | Enable debug output |

### Data Paths

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| CSV_EXPORT_DIR | string | ./exports | CSV export directory |
| CSV_IMPORT_DIR | string | ./imports | CSV import directory |
| IMAGE_BASE_DIR | string | ./data/images | Base directory for product images |
| LOG_DIR | string | ./logs | Application log directory |

---

## Troubleshooting

### Configuration Not Loading

**Problem**: Application says "API key not found"

**Solution**:
1. Verify `.env` exists: `Test-Path C:\Users\nario\.marginscount\.env`
2. Verify format: `type C:\Users\nario\.marginscount\.env`
3. Check for syntax errors (quotes, special characters)
4. Restart application after editing `.env`

### Permission Denied

**Problem**: Cannot read `.env` file

**Solution**:
```powershell
# Fix permissions (user only)
icacls C:\Users\nario\.marginscount /grant:r %USERNAME%:F /inheritance:r
```

### Multiple Users on Same Machine

**Problem**: Different users need different credentials

**Solution**:
Each user creates their own `.env`:
- User A: `C:\Users\UserA\.marginscount\.env`
- User B: `C:\Users\UserB\.marginscount\.env`

---

## .env Example

```bash
# Development Environment
APP_ENV=development
LOG_LEVEL=DEBUG
DEBUG_MODE=true

# eBay Sandbox (Development)
EBAY_SANDBOX_CLIENT_ID=your_sandbox_id_here
EBAY_SANDBOX_CLIENT_SECRET=your_sandbox_secret_here
EBAY_APP_ID=your_app_id_here

# Paths
CSV_EXPORT_DIR=./exports
CSV_IMPORT_DIR=./imports
IMAGE_BASE_DIR=./data/images
LOG_DIR=./logs

# Logging
AUDIT_LOG_FILE=./logs/execution_audit.jsonl
```

---

## Related Files

- **Project README**: See root `README.md` for project overview
- **Project Origin**: See `docs/PROJECT_ORIGIN.md` for project heritage
- **Development Guide**: See `docs/DEVELOPMENT.md` (future)

---

**Last Updated**: 2026-06-13  
**Version**: 1.0  
