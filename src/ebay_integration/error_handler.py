"""eBay API エラーハンドリング"""
import logging

class EbayApiException(Exception):
    """eBay API エラーベースクラス"""
    pass

class EbayAuthException(EbayApiException):
    """認証エラー"""
    pass

class EbayRateLimitException(EbayApiException):
    """レート制限"""
    pass

class EbaySearchException(EbayApiException):
    """検索エラー"""
    pass

def handle_api_error(response):
    """HTTP レスポンスからエラーを判定"""
    if response.status_code == 401:
        raise EbayAuthException(f"Auth failed: {response.text}")
    elif response.status_code == 429:
        raise EbayRateLimitException(f"Rate limited: {response.text}")
    elif response.status_code >= 400:
        raise EbaySearchException(f"API error: {response.status_code} - {response.text}")
