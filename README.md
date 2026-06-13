# MarginScout


---

## Setup & Configuration

### Quick Start

1. **Clone or navigate to the repository**
   ```bash
   cd margin-scout
   ```

2. **Create user configuration directory**
   ```powershell
   # Automatically created, but verify:
   Test-Path C:\Users\nario\.marginscount
   ```

3. **Configure environment variables**
   ```bash
   # Copy template to user home directory
   Copy-Item .env.example C:\Users\nario\.marginscount\.env
   
   # Edit with your API keys
   notepad C:\Users\nario\.marginscount\.env
   ```

4. **Verify configuration**
   ```bash
   python verify_config.py
   ```

### Configuration Details

See **docs/CONFIGURATION.md** for detailed setup instructions, security best practices, and troubleshooting.

### Environment Variables

**User Configuration Location:**
```
C:\Users\{ユーザ名}\.marginscount\.env
```

**Required for eBay Integration:**
- `EBAY_SANDBOX_CLIENT_ID`
- `EBAY_SANDBOX_CLIENT_SECRET`
- `EBAY_APP_ID`

**Optional:**
- `EBAY_CERT_ID`
- `EBAY_DEV_ID`
- `APP_ENV` (default: development)
- `LOG_LEVEL` (default: INFO)

See **docs/CONFIGURATION.md** for full reference.
