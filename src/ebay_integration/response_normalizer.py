"""eBay API レスポンスを MarginScout 用に正規化"""
from typing import Dict, List, Optional
from decimal import Decimal

class EbayResponseNormalizer:
    """eBay API レスポンスを内部データ構造に変換"""
    
    @staticmethod
    def normalize_search_item(item: Dict) -> Dict:
        """
        search 結果から単一アイテムを正規化
        
        Returns:
            {
                "item_id": str,
                "title": str,
                "price": Decimal,
                "currency": str,
                "condition": str,
                "category": str,
                "image_url": str,
                "item_url": str,
                "seller_rating": float,
            }
        """
        price_obj = item.get("price", {})
        price = Decimal(str(price_obj.get("value", 0)))
        
        return {
            "item_id": item.get("itemId"),
            "title": item.get("title"),
            "price": price,
            "currency": price_obj.get("currency", "USD"),
            "condition": item.get("condition"),
            "category": item.get("categoryId"),
            "image_url": item.get("image", {}).get("imageUrl"),
            "item_url": item.get("itemWebUrl"),
            "seller_rating": item.get("seller", {}).get("feedbackPercentage"),
        }
    
    @staticmethod
    def normalize_get_item(item: Dict) -> Dict:
        """
        getItem 結果から詳細情報を正規化
        
        Returns:
            詳細情報を含む辞書
        """
        price_obj = item.get("price", {})
        price = Decimal(str(price_obj.get("value", 0)))
        
        return {
            "item_id": item.get("itemId"),
            "title": item.get("title"),
            "price": price,
            "currency": price_obj.get("currency", "USD"),
            "condition": item.get("condition"),
            "category": item.get("category"),
            "description": item.get("description"),
            "item_url": item.get("itemWebUrl"),
            "seller": item.get("seller", {}).get("username"),
            "seller_rating": item.get("seller", {}).get("feedbackPercentage"),
            "shipping_cost": Decimal(str(item.get("shippingOptions", [{}])[0].get("shippingCost", {}).get("value", 0))),
        }
