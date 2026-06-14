#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Configuration Unification & Sandbox Connection Test
- config_loader.py と Phase 6 実装の統一
- 後方互換性確保
- 正式な .env 配置場所確定
- Sandbox 接続テスト実行
"""

import os
import json
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION UNIFICATION
# ============================================================================

def unify_config_loader():
    """統一された config_loader.py を作成"""
    
    code = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Configuration Loader (Unified)
環境変数を統一キーで読み込む（後方互換性あり）
"""

import os
from pathlib import Path
from typing import Optional

class ConfigLoader:
    """統一設定ローダー"""
    
    # 公式環境変数キー（Phase 6 仕様）
    OFFICIAL_KEYS = {
        'ebay_env': 'EBAY_ENV',
        'ebay_client_id': 'EBAY_CLIENT_ID',
        'ebay_client_secret': 'EBAY_CLIENT_SECRET',
        'ebay_redirect_uri': 'EBAY_REDIRECT_URI',
        'ebay_refresh_token': 'EBAY_REFRESH_TOKEN',
        'ebay_request_timeout': 'EBAY_REQUEST_TIMEOUT',
        'ebay_max_retries': 'EBAY_MAX_RETRIES',
    }
    
    # 後方互換キー（旧キー名）
    LEGACY_KEYS = {
        'ebay_client_id': ['EBAY_SANDBOX_CLIENT_ID', 'EBAY_APP_ID'],
        'ebay_client_secret': ['EBAY_SANDBOX_CLIENT_SECRET'],
        'ebay_env': ['EBAY_ENVIRONMENT'],
    }
    
    # 正式 .env 配置場所
    ENV_PATHS = [
        Path.home() / '.marginscount' / '.env',  # 推奨：ホームディレクトリ
        Path.cwd() / '.env',                       # フォールバック：プロジェクトディレクトリ
    ]
    
    @classmethod
    def get_env_file_path(cls) -> Optional[Path]:
        """正式な .env ファイルパスを取得"""
        for env_path in cls.ENV_PATHS:
            if env_path.exists():
                return env_path
        return cls.ENV_PATHS[0]  # デフォルト：ホームディレクトリ
    
    @classmethod
    def load_from_file(cls) -> dict:
        """ファイルから設定を読み込む"""
        env_file = cls.get_env_file_path()
        config = {}
        
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
        
        return config
    
    @classmethod
    def get_value(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        統一キーで環境変数を取得
        優先順: 環境変数 → ファイル設定 → 後方互換キー → デフォルト
        """
        # 1. 公式キーで環境変数を確認
        if key in cls.OFFICIAL_KEYS:
            official_key = cls.OFFICIAL_KEYS[key]
            if official_key in os.environ:
                return os.environ[official_key]
        
        # 2. ファイルから読込
        file_config = cls.load_from_file()
        if key in cls.OFFICIAL_KEYS:
            official_key = cls.OFFICIAL_KEYS[key]
            if official_key in file_config:
                return file_config[official_key]
        
        # 3. 後方互換キーを確認
        if key in cls.LEGACY_KEYS:
            for legacy_key in cls.LEGACY_KEYS[key]:
                if legacy_key in os.environ:
                    print(f"[Config] Using legacy key {legacy_key} (deprecated, use {cls.OFFICIAL_KEYS.get(key, key)} instead)")
                    return os.environ[legacy_key]
                if legacy_key in file_config:
                    print(f"[Config] Using legacy key {legacy_key} (deprecated, use {cls.OFFICIAL_KEYS.get(key, key)} instead)")
                    return file_config[legacy_key]
        
        # 4. デフォルト値
        return default
    
    @classmethod
    def get_ebay_env(cls) -> str:
        """eBay環境（sandbox/production）を取得"""
        return cls.get_value('ebay_env', 'sandbox')
    
    @classmethod
    def get_ebay_client_id(cls) -> str:
        """eBay Client ID を取得"""
        value = cls.get_value('ebay_client_id')
        if not value:
            raise ValueError("EBAY_CLIENT_ID not found in environment or .env")
        return value
    
    @classmethod
    def get_ebay_client_secret(cls) -> str:
        """eBay Client Secret を取得"""
        value = cls.get_value('ebay_client_secret')
        if not value:
            raise ValueError("EBAY_CLIENT_SECRET not found in environment or .env")
        return value
    
    @classmethod
    def get_ebay_redirect_uri(cls) -> str:
        """eBay Redirect URI を取得"""
        return cls.get_value('ebay_redirect_uri', 'http://localhost:8080/callback')
    
    @classmethod
    def get_ebay_refresh_token(cls) -> Optional[str]:
        """eBay Refresh Token を取得（オプション）"""
        return cls.get_value('ebay_refresh_token')
    
    @classmethod
    def get_config_summary(cls) -> dict:
        """設定サマリーを取得（マスク済み）"""
        return {
            'env_file_path': str(cls.get_env_file_path()),
            'ebay_env': cls.get_ebay_env(),
            'ebay_client_id': cls.get_ebay_client_id()[:10] + '...' if cls.get_value('ebay_client_id') else 'NOT SET',
            'ebay_client_secret': '***masked***' if cls.get_value('ebay_client_secret') else 'NOT SET',
            'ebay_redirect_uri': cls.get_ebay_redirect_uri(),
            'ebay_refresh_token': '***masked***' if cls.get_ebay_refresh_token() else 'NOT SET',
        }

# グローバルローダーインスタンス
config = ConfigLoader()

if __name__ == '__main__':
    print("MarginScout Configuration Loader")
    print("="*70)
    print(json.dumps(config.get_config_summary(), indent=2))
'''
    
    config_path = Path.cwd() / 'src' / 'config_loader.py'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print("✓ src/config_loader.py unified")
    return config_path

def create_sandbox_test():
    """Sandbox 接続テストスクリプトを作成"""
    
    code = r'''#!/usr/bin/env python3
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
'''
    
    test_path = Path.cwd() / 'sandbox_connection_test.py'
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print("✓ sandbox_connection_test.py created")
    return test_path

def update_documentation():
    """ドキュメントを更新"""
    
    # CONFIGURATION.md 更新
    config_md = r'''# MarginScout Configuration Guide

## 正式な .env 配置場所

**推奨（デフォルト）:**
```
C:\Users\{username}\.marginscount\.env
```

**フォールバック:**
```
{project_root}\.env
```

## Phase 6: eBay OAuth & Live API 設定

### 統一された環境変数キー

MarginScout は以下の **公式環境変数キー** を使用します：

| 変数名 | 説明 | 必須 | 例 |
|--------|------|------|-----|
| EBAY_ENV | 環境（sandbox/production） | No | sandbox |
| EBAY_CLIENT_ID | eBay App ID | Yes | AppId_123456 |
| EBAY_CLIENT_SECRET | eBay Cert ID | Yes | CertId_abcdef |
| EBAY_REDIRECT_URI | OAuth redirect URI | No | http://localhost:8080/callback |
| EBAY_REFRESH_TOKEN | eBay refresh token | No* | v^1.1#i^1#... |
| EBAY_REQUEST_TIMEOUT | API request timeout秒 | No | 30 |
| EBAY_MAX_RETRIES | API retry回数 | No | 3 |

*EBAY_REFRESH_TOKEN は Phase 6 live API 呼び出し時に必須です。

### .env ファイル作成手順

1. **ホームディレクトリに .marginscount フォルダを作成:**
```bash
mkdir -p ~/.marginscount
```

2. **.env ファイルを作成:**
```bash
cat > ~/.marginscount/.env << EOF
EBAY_ENV=sandbox
EBAY_CLIENT_ID=your_app_id_here
EBAY_CLIENT_SECRET=your_cert_id_here
EBAY_REDIRECT_URI=http://localhost:8080/callback
EBAY_REFRESH_TOKEN=
EBAY_REQUEST_TIMEOUT=30
EBAY_MAX_RETRIES=3
EOF
```

3. **パーミッション設定（Unix/Linux/Mac）:**
```bash
chmod 600 ~/.marginscount/.env
```

### 後方互換性

以下の旧キー名も読込可能です（非推奨）：
- EBAY_SANDBOX_CLIENT_ID → EBAY_CLIENT_ID に統合
- EBAY_SANDBOX_CLIENT_SECRET → EBAY_CLIENT_SECRET に統合
- EBAY_APP_ID → EBAY_CLIENT_ID に統合

新規プロジェクトは公式キー名を使用してください。

### 設定確認

```bash
python -m src.config_loader
```

出力例:
```json
{
  "env_file_path": "C:\\Users\\username\\.marginscount\\.env",
  "ebay_env": "sandbox",
  "ebay_client_id": "AppId_123...",
  "ebay_client_secret": "***masked***",
  "ebay_redirect_uri": "http://localhost:8080/callback",
  "ebay_refresh_token": "***masked***"
}
```

## Sandbox Connection Test

```bash
python sandbox_connection_test.py
```

テスト項目:
1. Configuration Loading
2. OAuth Handler Initialization
3. API Client Initialization
4. Token Configuration Check
'''
    
    config_path = Path.cwd() / 'docs' / 'CONFIGURATION.md'
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_md)
    
    print("✓ docs/CONFIGURATION.md updated")

def main():
    print("\nPhase 1: Configuration Unification")
    unify_config_loader()
    
    print("\nPhase 2: Sandbox Test Script Creation")
    create_sandbox_test()
    
    print("\nPhase 3: Documentation Update")
    update_documentation()
    
    print("\n" + "="*70)
    print("Configuration Unification: COMPLETE")
    print("="*70)
    
    print("\nNext: Run sandbox_connection_test.py")
    print("  python sandbox_connection_test.py")

if __name__ == '__main__':
    main()
