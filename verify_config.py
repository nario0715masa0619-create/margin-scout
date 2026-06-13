import sys
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
