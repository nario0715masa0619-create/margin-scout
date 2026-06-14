"""eBay 検索と候補抽出のオーケストレーション"""
from typing import Dict, List, Optional
from decimal import Decimal
import logging

from src.ebay_integration import EbayBrowseApiClient, EbayResponseNormalizer
from .product_matcher import ProductMatcher

class EbaySearcher:
    """eBay での検索と商品マッチングを実行"""
    
    def __init__(self, ebay_client: EbayBrowseApiClient):
        self.ebay_client = ebay_client
        self.normalizer = EbayResponseNormalizer()
        self.matcher = ProductMatcher()
        self.logger = logging.getLogger(__name__)
    
    def search_and_match(self, source_product: Dict) -> Optional[Dict]:
        """
        仕入れ元商品を eBay で検索してマッチングを実行
        
        Args:
            source_product: {
                "product_name": str,
                "brand": Optional[str],
                "model_number": Optional[str],
                "category": Optional[str],
                "condition": Optional[str],
            }
        
        Returns:
            マッチングに成功した eBay 商品情報、または None
        """
        try:
            # 検索クエリを生成
            query = self.matcher.generate_search_query(source_product)
            
            # eBay で検索
            self.logger.info(f"Searching eBay for: {query}")
            search_response = self.ebay_client.search(query, limit=50)
            
            # 検索結果を正規化
            items = search_response.get("itemSummaries", [])
            normalized_items = [
                self.normalizer.normalize_search_item(item)
                for item in items
            ]
            
            # マッチング実行
            matched_item, confidence = self.matcher.match_items(
                source_product,
                normalized_items
            )
            
            if matched_item:
                # 詳細情報を取得
                detail_response = self.ebay_client.get_item(matched_item["item_id"])
                matched_item_detail = self.normalizer.normalize_get_item(detail_response)
                matched_item_detail["match_confidence"] = confidence
                
                return matched_item_detail
            else:
                self.logger.warning(f"No good match found for: {source_product.get('product_name')}")
                return None
        
        except Exception as e:
            self.logger.error(f"Error searching eBay: {e}")
            return None
    
    def calculate_profit(
        self,
        source_price: Decimal,
        ebay_price: Decimal,
        source_currency: str = "JPY",
        ebay_currency: str = "USD"
    ) -> Dict:
        """
        利益を計算
        
        Args:
            source_price: 仕入れ価格
            ebay_price: eBay 販売価格
            source_currency: 仕入れ側通貨
            ebay_currency: eBay 側通貨
        
        Returns:
            {
                "estimated_profit": Decimal,
                "profit_margin_percent": float,
                "shipping_estimate": Decimal,
                "fee_estimate": Decimal,
            }
        """
        # 簡易的な為替計算（本来は外部APIを使うべき）
        # ここでは 1 USD = 150 JPY と仮定
        exchange_rate = 150.0 if source_currency == "JPY" and ebay_currency == "USD" else 1.0
        
        source_price_usd = source_price / Decimal(str(exchange_rate)) if source_currency == "JPY" else source_price
        
        # 推定手数料と送料（簡易値）
        fee_estimate = ebay_price * Decimal("0.15")  # 15% 手数料（推定）
        shipping_estimate = Decimal("10.0")  # $10 送料（推定）
        
        # 利益計算
        net_revenue = ebay_price - fee_estimate - shipping_estimate
        estimated_profit = net_revenue - source_price_usd
        
        # 利益率
        if net_revenue > 0:
            profit_margin_percent = float((estimated_profit / net_revenue) * 100)
        else:
            profit_margin_percent = -100.0
        
        return {
            "estimated_profit": estimated_profit,
            "profit_margin_percent": profit_margin_percent,
            "shipping_estimate": shipping_estimate,
            "fee_estimate": fee_estimate,
        }
