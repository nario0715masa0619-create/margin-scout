#!/usr/bin/env python3
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
