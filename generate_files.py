import os
import pathlib

username = os.environ.get('USERNAME', 'nario')
project_dir = pathlib.Path('C:/NewProjects/margin-scout')
config_dir = pathlib.Path(f'C:/Users/{username}/.marginscount')

# 1. Create config dir
config_dir.mkdir(parents=True, exist_ok=True)

# 2. .env
env_content = f'''# MarginScout Environment Configuration
# Location: C:\\Users\\{username}\\.marginscount\\.env
# 
# DO NOT commit this file to version control
# This file contains sensitive information (API keys, secrets)

# ====================================================================
# eBay API Configuration (Sandbox)
# ====================================================================
EBAY_SANDBOX_CLIENT_ID=your_sandbox_client_id
EBAY_SANDBOX_CLIENT_SECRET=your_sandbox_client_secret
EBAY_APP_ID=your_app_id
EBAY_CERT_ID=your_cert_id
EBAY_DEV_ID=your_dev_id

# ====================================================================
# eBay API Configuration (Production - if applicable)
# ====================================================================
# EBAY_PROD_CLIENT_ID=your_prod_client_id
# EBAY_PROD_CLIENT_SECRET=your_prod_client_secret

# ====================================================================
# Application Settings
# ====================================================================
APP_ENV=development
LOG_LEVEL=INFO
DEBUG_MODE=false

# ====================================================================
# Database Configuration (if applicable)
# ====================================================================
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=marginscount_dev
# DB_USER=user
# DB_PASSWORD=password

# ====================================================================
# Research Data Sources (future)
# ====================================================================
# PRICING_API_KEY=
# MARKET_DATA_SOURCE=

# ====================================================================
# CSV Configuration
# ====================================================================
CSV_EXPORT_DIR=./exports
CSV_IMPORT_DIR=./imports
CSV_DELIMITER=,

# ====================================================================
# Image Configuration
# ====================================================================
IMAGE_BASE_DIR=./data/images
SUPPORTED_IMAGE_EXTENSIONS=jpg,jpeg,png
MAX_IMAGE_SIZE_MB=10

# ====================================================================
# Logging
# ====================================================================
LOG_DIR=./logs
AUDIT_LOG_FILE=./logs/execution_audit.jsonl
'''
(config_dir / '.env').write_text(env_content, encoding='utf-8')

# 3. .gitignore
gitignore_content = '''# Environment
.env
.env.local
.env.*.local

# User configuration (stored outside repo)
# .marginscount/ directory in user home is intentionally excluded from version control

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Poetry
poetry.lock

# OS
.DS_Store
Thumbs.db

# Project specific
*.log
.tmp/
temp_*.py
exports/
imports/
'''
(project_dir / '.gitignore').write_text(gitignore_content, encoding='utf-8')

# 4. docs/CONFIGURATION.md
docs_dir = project_dir / 'docs'
docs_dir.mkdir(parents=True, exist_ok=True)
config_doc_content = f'''# MarginScout Environment Configuration Guide

## Overview

MarginScout stores environment configuration (API keys, secrets, etc.) outside the project repository for security reasons.

Configuration files are stored in the user's home directory:
- **Location**: `C:\\Users\\{{ユーザ名}}\\.marginscount\\.env`
- **Access**: Local user only
- **Version Control**: NOT tracked in Git (security)

---

## Setup Instructions

### 1. Configuration Directory

The configuration directory is automatically created at:
```
C:\\Users\\{username}\\.marginscount\\
```

### 2. Environment File

Create or edit the `.env` file:
```
C:\\Users\\{username}\\.marginscount\\.env
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
   C:\\Users\\{{ユーザ名}}\\.marginscount\\.env
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
- ✓ Restrict file permissions: `icacls C:\\Users\\{{ユーザ名}}\\.marginscount /grant:r %USERNAME%:F /inheritance:r`
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
C:\\Users\\{{ユーザ名}}\\
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
1. Verify `.env` exists: `Test-Path C:\\Users\\{username}\\.marginscount\\.env`
2. Verify format: `type C:\\Users\\{username}\\.marginscount\\.env`
3. Check for syntax errors (quotes, special characters)
4. Restart application after editing `.env`

### Permission Denied

**Problem**: Cannot read `.env` file

**Solution**:
```powershell
# Fix permissions (user only)
icacls C:\\Users\\{username}\\.marginscount /grant:r %USERNAME%:F /inheritance:r
```

### Multiple Users on Same Machine

**Problem**: Different users need different credentials

**Solution**:
Each user creates their own `.env`:
- User A: `C:\\Users\\UserA\\.marginscount\\.env`
- User B: `C:\\Users\\UserB\\.marginscount\\.env`

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
'''
(docs_dir / 'CONFIGURATION.md').write_text(config_doc_content, encoding='utf-8')

# 5. .env.example
env_example_content = '''# MarginScout Environment Configuration Template
# 
# This file serves as a template showing required environment variables.
# 
# To use:
# 1. Copy this file to C:\\Users\\{ユーザ名}\\.marginscount\\.env
# 2. Fill in your actual API keys and configuration
# 3. DO NOT commit the actual .env file to Git
#
# See docs/CONFIGURATION.md for detailed setup instructions

# ====================================================================
# eBay API Configuration (Sandbox - for development)
# ====================================================================
EBAY_SANDBOX_CLIENT_ID=
EBAY_SANDBOX_CLIENT_SECRET=
EBAY_APP_ID=
EBAY_CERT_ID=
EBAY_DEV_ID=

# ====================================================================
# eBay API Configuration (Production - optional)
# ====================================================================
# EBAY_PROD_CLIENT_ID=
# EBAY_PROD_CLIENT_SECRET=

# ====================================================================
# Application Settings
# ====================================================================
APP_ENV=development
LOG_LEVEL=INFO
DEBUG_MODE=false

# ====================================================================
# Data Paths
# ====================================================================
CSV_EXPORT_DIR=./exports
CSV_IMPORT_DIR=./imports
IMAGE_BASE_DIR=./data/images
LOG_DIR=./logs

# ====================================================================
# Logging
# ====================================================================
AUDIT_LOG_FILE=./logs/execution_audit.jsonl
'''
(project_dir / '.env.example').write_text(env_example_content, encoding='utf-8')

# 6. src/config_loader.py
src_dir = project_dir / 'src'
src_dir.mkdir(parents=True, exist_ok=True)
config_loader_content = '''import os
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    """
    Load MarginScout configuration from multiple sources.
    
    Priority (highest to lowest):
    1. User home directory: C:\\Users\\{ユーザ名}\\.marginscount\\.env
    2. Project directory: .env (if exists, for development only)
    3. Environment variables
    4. Default values
    """
    
    def __init__(self):
        self.username = os.getenv('USERNAME', 'unknown')
        self.config_dir = Path.home() / '.marginscount'
        self.project_env_file = Path('.env')
        self.user_env_file = self.config_dir / '.env'
        
        self._load_config()
    
    def _load_config(self):
        """Load configuration from all sources."""
        
        # 1. User home directory configuration
        if self.user_env_file.exists():
            load_dotenv(self.user_env_file, override=True)
            print(f'✓ Loaded user config: {self.user_env_file}')
        else:
            print(f'⚠ User config not found: {self.user_env_file}')
            print(f'  Create it at: C:\\\\Users\\\\{self.username}\\\\.marginscount\\\\.env')
        
        # 2. Project .env (development only, optional)
        if self.project_env_file.exists():
            load_dotenv(self.project_env_file, override=False)
            print(f'✓ Loaded project config: {self.project_env_file}')
    
    def get(self, key, default=None):
        """Get configuration value."""
        return os.getenv(key, default)
    
    def get_ebay_sandbox_credentials(self):
        """Get eBay Sandbox credentials."""
        return {
            'client_id': self.get('EBAY_SANDBOX_CLIENT_ID'),
            'client_secret': self.get('EBAY_SANDBOX_CLIENT_SECRET'),
            'app_id': self.get('EBAY_APP_ID'),
        }
    
    def validate_ebay_credentials(self):
        """Validate that required eBay credentials are set."""
        required_keys = [
            'EBAY_SANDBOX_CLIENT_ID',
            'EBAY_SANDBOX_CLIENT_SECRET',
            'EBAY_APP_ID',
        ]
        
        missing = [key for key in required_keys if not self.get(key)]
        
        if missing:
            raise ValueError(
                f'Missing required eBay credentials: {missing}\\n'
                f'Please set them in: {self.user_env_file}'
            )
        
        return True


# Example usage:
if __name__ == '__main__':
    config = ConfigLoader()
    
    try:
        config.validate_ebay_credentials()
        print('✓ eBay credentials validated')
    except ValueError as e:
        print(f'✗ Configuration error: {e}')
'''
(src_dir / 'config_loader.py').write_text(config_loader_content, encoding='utf-8')

# 7. verify_config.py
verify_config_content = '''import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from config_loader import ConfigLoader
    
    print('=' * 60)
    print('MarginScout Configuration Verification')
    print('=' * 60)
    print('')
    
    config = ConfigLoader()
    
    print(f'Configuration Directory: {config.config_dir}')
    print(f'User Config File: {config.user_env_file}')
    print(f'User Config Exists: {config.user_env_file.exists()}')
    print('')
    
    print('Environment Variables Loaded:')
    ebay_creds = config.get_ebay_sandbox_credentials()
    print(f'  EBAY_SANDBOX_CLIENT_ID: {"SET" if ebay_creds["client_id"] else "NOT SET"}')
    print(f'  EBAY_SANDBOX_CLIENT_SECRET: {"SET" if ebay_creds["client_secret"] else "NOT SET"}')
    print(f'  EBAY_APP_ID: {"SET" if ebay_creds["app_id"] else "NOT SET"}')
    print('')
    
    try:
        config.validate_ebay_credentials()
        print('✓ eBay Credentials: VALID')
    except ValueError as e:
        print(f'✗ eBay Credentials: MISSING - {e}')
    
    print('')
    print('Other Configuration:')
    print(f'  APP_ENV: {config.get("APP_ENV", "development")}')
    print(f'  LOG_LEVEL: {config.get("LOG_LEVEL", "INFO")}')
    print(f'  DEBUG_MODE: {config.get("DEBUG_MODE", "false")}')
    print('')
    print('=' * 60)
    
except ImportError as e:
    print(f'Error: Could not import ConfigLoader: {e}')
    sys.exit(1)
'''
(project_dir / 'verify_config.py').write_text(verify_config_content, encoding='utf-8')

# 8. Update README.md
readme_path = project_dir / 'README.md'
if not readme_path.exists():
    readme_path.write_text('# MarginScout\n', encoding='utf-8')

readme_content = readme_path.read_text(encoding='utf-8')
setup_section = f'''

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
   Test-Path C:\\Users\\{username}\\.marginscount
   ```

3. **Configure environment variables**
   ```bash
   # Copy template to user home directory
   Copy-Item .env.example C:\\Users\\{username}\\.marginscount\\.env
   
   # Edit with your API keys
   notepad C:\\Users\\{username}\\.marginscount\\.env
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
C:\\Users\\{{ユーザ名}}\\.marginscount\\.env
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
'''
readme_path.write_text(readme_content + setup_section, encoding='utf-8')
