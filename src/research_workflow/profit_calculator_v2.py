"""
Profit Calculator v2 - eBay 出品時の正確な利益計算
shipping_calculator.py と連携
"""

from src.research_workflow.shipping_calculator import ShippingCalculator

class ProfitCalculatorV2:
    """eBay 出品・売却時の利益計算"""
    
    # eBay Managed Payments - 出品手数料
    EBAY_FINAL_VALUE_FEE_RATE = 0.136  # 13.6%
    EBAY_FINAL_VALUE_FEE_FIXED = 0.40  # $0.40 USD
    
    def __init__(self, exchange_rate: float = 157.50):
        self.exchange_rate = exchange_rate
        self.shipping_calc = ShippingCalculator(exchange_rate)
    
    def calculate_profit(self, ebay_price_usd: float, source_price_jpy: float, 
                        weight_grams: int = None, category: str = None) -> dict:
        """
        eBay 売却時の利益を計算
        
        Args:
            ebay_price_usd: eBay での売却価格（USD）
            source_price_jpy: 仕入れ元での仕入れ価格（JPY）
            weight_grams: 商品重さ（グラム）. None の場合はカテゴリから推定
            category: 商品カテゴリ（electronics, camera, games, fashion, hobby）
        
        Returns:
            利益計算結果の辞書
        """
        
        # 重さの推定
        if weight_grams is None:
            if category:
                weight_grams = self.shipping_calc.estimate_weight_from_category(category)
            else:
                weight_grams = 500  # デフォルト
        
        # eBay 売却収入（JPY）
        ebay_revenue_jpy = ebay_price_usd * self.exchange_rate
        
        # eBay Final Value Fee (USD → JPY)
        fvf_usd = (ebay_price_usd * self.EBAY_FINAL_VALUE_FEE_RATE) + self.EBAY_FINAL_VALUE_FEE_FIXED
        fvf_jpy = fvf_usd * self.exchange_rate
        
        # 送料計算（実際のキャリアレート）
        shipping_result = self.shipping_calc.get_optimal_shipping(weight_grams)
        shipping_jpy = shipping_result['shipping_jpy']
        carrier = shipping_result['carrier']
        
        # 総費用
        total_expenses_jpy = fvf_jpy + shipping_jpy + source_price_jpy
        
        # 最終利益
        profit_jpy = ebay_revenue_jpy - total_expenses_jpy
        
        # 利益率（eBay 売却価格に対する率）
        if ebay_revenue_jpy > 0:
            profit_margin_pct = (profit_jpy / ebay_revenue_jpy) * 100
        else:
            profit_margin_pct = -100.0
        
        return {
            "ebay_price_usd": ebay_price_usd,
            "ebay_revenue_jpy": round(ebay_revenue_jpy, 2),
            "ebay_fvf_jpy": round(fvf_jpy, 2),
            "shipping_jpy": round(shipping_jpy, 0),
            "shipping_carrier": carrier,
            "estimated_weight_g": weight_grams,
            "source_price_jpy": source_price_jpy,
            "total_expenses_jpy": round(total_expenses_jpy, 2),
            "profit_jpy": round(profit_jpy, 2),
            "profit_margin_pct": round(profit_margin_pct, 2)
        }
