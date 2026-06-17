"""商品マッチング基盤 - 仕入れ元商品と eBay 商品のマッチング"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
import logging

class ProductMatcher:
    """ルールベースの商品マッチングエンジン"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Threshold lowered from 0.5 to 0.4 as per Phase B
        self.min_match_score = 0.4
    
    def generate_search_query(self, source_product: Dict) -> str:
        """
        [DEPRECATED] QueryOptimizer.generate_queries を代わりに使用してください。
        互換性のために残しています。
        """
        return source_product.get("product_name", "product")
    
    def match_items(
        self,
        source_product: Dict,
        ebay_search_results: List[Dict],
        source_price_jpy: Optional[float] = None
    ) -> Tuple[Optional[Dict], float]:
        """
        eBay 検索結果から最適な商品を選択
        
        Args:
            source_product: 仕入れ元商品
            ebay_search_results: eBay search API の結果リスト
            source_price_jpy: 仕入れ価格（価格チェック用）
        
        Returns:
            (最適な eBay 商品, 信頼度スコア)
        """
        if not ebay_search_results:
            return None, 0.0
        
        best_match = None
        best_score = 0.0
        
        for ebay_item in ebay_search_results:
            # 価格チェック（10倍以上の乖離があれば除外）
            if source_price_jpy is not None and source_price_jpy > 0:
                ebay_price_raw = ebay_item.get("price", {})
                ebay_price_usd = 0.0
                if isinstance(ebay_price_raw, dict):
                    ebay_price_usd = float(ebay_price_raw.get("value", 0))
                else:
                    ebay_price_usd = float(ebay_price_raw)
                    
                # 簡易的に 1 USD = 150 JPY として計算
                ebay_price_jpy_est = ebay_price_usd * 150
                
                # 異常な価格差（10倍以上違う）場合はスキップ
                if ebay_price_jpy_est > 0:
                    ratio = source_price_jpy / ebay_price_jpy_est
                    if ratio > 10.0 or ratio < 0.1:
                        self.logger.debug(f"Skipping due to extreme price difference: JPY {source_price_jpy} vs USD {ebay_price_usd}")
                        continue

            score = self._calculate_match_score(source_product, ebay_item)
            
            # 完全一致レベルなら即時採用（1.0）
            if score >= 0.99:
                best_score = score
                best_match = ebay_item
                break
                
            if score > best_score:
                best_score = score
                best_match = ebay_item
        
        # 信頼度が低すぎる場合は除外
        if best_score < self.min_match_score:
            self.logger.warning(
                f"Match confidence too low ({best_score:.2%}) for {source_product.get('product_name')}"
            )
            return None, best_score
        
        self.logger.info(
            f"Matched: {source_product.get('product_name')} → {best_match.get('title')} (score: {best_score:.2%})"
        )
        
        return best_match, best_score
    
    def _calculate_match_score(self, source_product: Dict, ebay_item: Dict) -> float:
        """
        仕入れ元商品と eBay 商品のマッチングスコアを計算
        
        スコアは 0.0 ~ 1.0 の間
        """
        scores = []
        weights = []
        
        # 1. タイトルマッチ（50%）
        title_score = self._calculate_title_match(
            source_product.get("product_name", ""),
            ebay_item.get("title", "")
        )
        scores.append(title_score)
        weights.append(0.5)
        
        # 2. ブランドマッチ（20%）
        brand_score = self._calculate_brand_match(
            source_product.get("brand", ""),
            ebay_item.get("title", "")
        )
        scores.append(brand_score)
        weights.append(0.2)
        
        # 3. モデル番号マッチ（20%）
        model_score = self._calculate_model_match(
            source_product.get("model_number", ""),
            ebay_item.get("title", "")
        )
        scores.append(model_score)
        weights.append(0.2)
        
        # 4. 状態マッチ（10%）
        condition_score = self._calculate_condition_match(
            source_product.get("condition", ""),
            ebay_item.get("condition", "")
        )
        scores.append(condition_score)
        weights.append(0.1)
        
        # 重み付き平均スコア
        total_score = sum(s * w for s, w in zip(scores, weights))
        return total_score
    
    def _calculate_title_match(self, source_title: str, ebay_title: str) -> float:
        """
        タイトル間の類似度を計算（Jaccardの類似度）
        """
        source_words = set(source_title.lower().split())
        ebay_words = set(ebay_title.lower().split())
        
        if not source_words or not ebay_words:
            return 0.0
        
        intersection = len(source_words & ebay_words)
        union = len(source_words | ebay_words)
        
        similarity = intersection / union if union > 0 else 0.0
        
        # ボーナス: eBay タイトルが長めの方が信頼度が高い
        if len(ebay_title) > len(source_title):
            similarity = min(1.0, similarity * 1.1)
        
        return similarity
    
    def _calculate_brand_match(self, source_brand: str, ebay_title: str) -> float:
        """ブランドがタイトルに含まれているか"""
        if not source_brand:
            return 1.0  # ブランド情報がない場合は満点
        
        if source_brand.lower() in ebay_title.lower():
            return 1.0
        
        return 0.0
    
    def _calculate_model_match(self, source_model: str, ebay_title: str) -> float:
        """モデル番号がタイトルに含まれているか"""
        if not source_model:
            return 1.0  # モデル情報がない場合は満点
        
        if source_model.lower() in ebay_title.lower():
            return 1.0
        
        # 部分マッチも認める（例: "WH-1000" vs "WH-1000XM4"）
        if any(part in ebay_title.lower() for part in source_model.lower().split()):
            return 0.7
        
        return 0.0
    
    def _calculate_condition_match(self, source_condition: str, ebay_condition: str) -> float:
        """状態の一致度"""
        if not source_condition or not ebay_condition:
            return 1.0
        
        source_cond_lower = source_condition.lower()
        ebay_cond_lower = ebay_condition.lower()
        
        # 完全一致
        if source_cond_lower == ebay_cond_lower:
            return 1.0
        
        # 部分的なマッチ
        if "new" in source_cond_lower and "new" in ebay_cond_lower:
            return 1.0
        if "used" in source_cond_lower and "used" in ebay_cond_lower:
            return 1.0
        
        # 異なる状態
        if ("new" in source_cond_lower and "used" in ebay_cond_lower) or \
           ("used" in source_cond_lower and "new" in ebay_cond_lower):
            return 0.0
        
        return 0.5
