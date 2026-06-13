import os
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    """
    Load MarginScout configuration from multiple sources.
    
    Priority (highest to lowest):
    1. User home directory: C:\Users\{ユーザ名}\.marginscount\.env
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
            print(f'  Create it at: C:\\Users\\{self.username}\\.marginscount\\.env')
        
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
                f'Missing required eBay credentials: {missing}\n'
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
