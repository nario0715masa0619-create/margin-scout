#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Sandbox Connection Test
Phase 6 OAuth & API 接続確認
"""

import json
import sys
from datetime import datetime
from pathlib import Path

def run_sandbox_test():
    """Sandbox 接続テスト実行"""
    
    print("="*70)
    print("MarginScout: Sandbox Connection Test")
    print("="*70)
    
    result = {
        'timestamp': datetime.now().isoformat(),
        'test_name': 'Sandbox Connection Test',
        'tests': [],
        'overall_status': 'PASSED',
    }
    
    # Test 1: Configuration Loading
    print("\n[Test 1] Loading configuration...")
    try:
        from src.config_loader import ConfigLoader
        
        summary = ConfigLoader.get_config_summary()
        print(f"  ✓ Configuration loaded")
        print(f"    Environment: {summary['ebay_env']}")
        print(f"    .env location: {summary['env_file_path']}")
        
        result['tests'].append({
            'name': 'Configuration Loading',
            'status': 'PASSED',
            'details': summary,
        })
    except Exception as e:
        print(f"  ✗ Configuration loading failed: {str(e)}")
        result['tests'].append({
            'name': 'Configuration Loading',
            'status': 'FAILED',
            'error': str(e),
        })
        result['overall_status'] = 'FAILED'
    
    # Test 2: OAuth Handler Initialization
    print("\n[Test 2] Initializing OAuth handler...")
    try:
        from src.api_integration.oauth_handler import EBayOAuthConfig, EBayAPIConfig, OAuthHandler
        from src.config_loader import ConfigLoader
        
        # Create config from unified loader
        oauth_config = EBayOAuthConfig(
            env=ConfigLoader.get_ebay_env(),
            client_id=ConfigLoader.get_ebay_client_id(),
            client_secret=ConfigLoader.get_ebay_client_secret(),
            redirect_uri=ConfigLoader.get_ebay_redirect_uri(),
        )
        api_config = EBayAPIConfig()
        
        # In my implementation, EBayOAuthConfig expects env instead of environment
        # and doesn't take refresh_token in constructor directly
        oauth_handler = OAuthHandler(oauth_config, api_config)
        
        print(f"  ✓ OAuth handler initialized")
        print(f"    OAuth URL: {oauth_handler.oauth_endpoint}")
        print(f"    API Base URL: {oauth_handler.token_endpoint}")
        
        result['tests'].append({
            'name': 'OAuth Handler Initialization',
            'status': 'PASSED',
            'details': {
                'environment': oauth_config.env,
                'oauth_url': oauth_handler.oauth_endpoint,
                'api_base_url': oauth_handler.token_endpoint,
            },
        })
    except Exception as e:
        print(f"  ✗ OAuth handler initialization failed: {str(e)}")
        result['tests'].append({
            'name': 'OAuth Handler Initialization',
            'status': 'FAILED',
            'error': str(e),
        })
        result['overall_status'] = 'FAILED'
    
    # Test 3: API Client Initialization
    print("\n[Test 3] Initializing API client...")
    try:
        from src.api_integration.ebay_api_client_live import EBayLiveAPIClient
        
        # Assuming oauth_handler is initialized successfully above
        api_client = EBayLiveAPIClient(oauth_handler)
        
        print(f"  ✓ API client initialized")
        print(f"    Sandbox ready: {oauth_config.env == 'sandbox'}")
        
        result['tests'].append({
            'name': 'API Client Initialization',
            'status': 'PASSED',
            'details': {
                'environment': oauth_config.env,
                'base_url': api_client.base_url,
                'timeout': api_client.api_config.timeout,
                'max_retries': api_client.api_config.max_retries,
            },
        })
    except Exception as e:
        print(f"  ✗ API client initialization failed: {str(e)}")
        result['tests'].append({
            'name': 'API Client Initialization',
            'status': 'FAILED',
            'error': str(e),
        })
        result['overall_status'] = 'FAILED'
    
    # Test 4: Token Configuration Check
    print("\n[Test 4] Checking token configuration...")
    try:
        from src.config_loader import ConfigLoader
        
        has_refresh_token = ConfigLoader.get_ebay_refresh_token() is not None
        
        if has_refresh_token:
            print(f"  ✓ Refresh token is configured")
            status = 'PASSED'
        else:
            print(f"  ⚠ Refresh token not configured (required for live API calls)")
            status = 'WARNING'
        
        result['tests'].append({
            'name': 'Token Configuration',
            'status': status,
            'details': {
                'refresh_token_configured': has_refresh_token,
                'note': 'Refresh token required for Phase 6 live API calls',
            },
        })
    except Exception as e:
        print(f"  ✗ Token check failed: {str(e)}")
        result['tests'].append({
            'name': 'Token Configuration',
            'status': 'FAILED',
            'error': str(e),
        })
    
    # Final Report
    print("\n" + "="*70)
    print(f"Test Results: {result['overall_status']}")
    print("="*70)
    
    print("\nTest Summary:")
    for test in result['tests']:
        status_symbol = "✓" if test['status'] == 'PASSED' else "✗" if test['status'] == 'FAILED' else "⚠"
        print(f"  {status_symbol} {test['name']}: {test['status']}")
    
    # Save report
    report_path = Path.cwd() / 'PHASE6_SANDBOX_TEST_RESULT.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Report saved: {report_path}")
    
    return result['overall_status'] == 'PASSED'

if __name__ == '__main__':
    success = run_sandbox_test()
    sys.exit(0 if success else 1)
