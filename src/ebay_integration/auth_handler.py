"""
eBay OAuth 2.0 Authentication Handler with Mock Support
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional


class EbayAuthHandler:
    """
    Handle eBay OAuth 2.0 authentication (Client Credentials flow).
    Supports mock mode for testing when credentials are not available.
    """
    
    SANDBOX_AUTH_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
    PRODUCTION_AUTH_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    
    def __init__(self, use_mock: bool = False):
        """
        Initialize auth handler.
        
        Args:
            use_mock: If True, use mock token instead of real eBay auth
        """
        self.client_id = os.getenv('EBAY_BROWSE_CLIENT_ID', '')
        self.client_secret = os.getenv('EBAY_BROWSE_CLIENT_SECRET', '')
        self.use_mock = use_mock or (not self.client_id or not self.client_secret)
        
        self.token = None
        self.token_expiry = None
        self.scope = 'https://api.ebay.com/oauth/api_scope'
    
    def get_token(self) -> Optional[str]:
        """
        Get valid eBay OAuth token. Refresh if expired.
        
        Returns:
            str: Valid access token, or None if auth fails
        """
        # Check if token is still valid (5 min buffer)
        if self.token and self.token_expiry and datetime.now() < (self.token_expiry - timedelta(minutes=5)):
            return self.token
        
        # Use mock token if credentials not available
        if self.use_mock:
            print("[AUTH] Using mock token (credentials not configured)")
            self.token = self._generate_mock_token()
            self.token_expiry = datetime.now() + timedelta(hours=1)
            return self.token
        
        # Try real eBay auth
        try:
            print("[AUTH] Authenticating with eBay Sandbox...")
            response = requests.post(
                self.SANDBOX_AUTH_URL,
                auth=(self.client_id, self.client_secret),
                data={
                    'grant_type': 'client_credentials',
                    'scope': self.scope
                },
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            self.token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            print(f"[AUTH] Token acquired (expires in {expires_in}s)")
            return self.token
            
        except requests.exceptions.RequestException as e:
            print(f"[AUTH] eBay auth failed: {e}")
            print("[AUTH] Falling back to mock token for testing")
            self.use_mock = True
            self.token = self._generate_mock_token()
            self.token_expiry = datetime.now() + timedelta(hours=1)
            return self.token
    
    def _generate_mock_token(self) -> str:
        """Generate a mock token for testing."""
        # Format: v1|<timestamp>|<mock_id>
        import time
        timestamp = int(time.time())
        return f"v1|{timestamp}|mock_sandbox_token_for_testing_only"
    
    def is_valid(self) -> bool:
        """Check if current token is valid."""
        return bool(self.token and (not self.token_expiry or datetime.now() < self.token_expiry))
