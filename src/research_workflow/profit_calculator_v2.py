"""
Profit Calculator v2 - eBay 出品時の正確な利益計算
（MarginScout: リサーチ専用）

梱包資材：無料（段ボール・FedEx無料資材など）
"""

class ProfitCalculatorV2:
    """eBay 出品・売却時の利益計算"""
    
    # eBay Managed Payments - 出品手数料
    EBAY_FINAL_VALUE_FEE_RATE = 0.136  # 13.6%
    EBAY_FINAL_VALUE_FEE_FIXED = 0.40  # $0.40 USD
    
    # Shipping & Logistics
    INTERNATIONAL_SHIPPING_USD = 20.0  # 国際送料（日本→米国、平均）
    
    def __init__(self, exchange_rate: float = 157.50):
        self.exchange_rate = exchange_rate
    
    def calculate_profit(self, ebay_price_usd: float, source_price_jpy: float) -> dict:
        """
        eBay 売却時の利益を計算
        
        Args:
            ebay_price_usd: eBay での売却価格（USD）
            source_price_jpy: 仕入れ元での仕入れ価格（JPY）
        
        Returns:
            利益計算結果の辞書
        """
        
        # eBay 売却収入（JPY）
        ebay_revenue_jpy = ebay_price_usd * self.exchange_rate
        
        # eBay Final Value Fee (USD → JPY)
        fvf_usd = (ebay_price_usd * self.EBAY_FINAL_VALUE_FEE_RATE) + self.EBAY_FINAL_VALUE_FEE_FIXED
        fvf_jpy = fvf_usd * self.exchange_rate
        
        # 国際送料 (USD → JPY)
        shipping_usd = self.INTERNATIONAL_SHIPPING_USD
        shipping_jpy = shipping_usd * self.exchange_rate
        
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
            "shipping_jpy": round(shipping_jpy, 2),
            "source_price_jpy": source_price_jpy,
            "total_expenses_jpy": round(total_expenses_jpy, 2),
            "profit_jpy": round(profit_jpy, 2),
            "profit_margin_pct": round(profit_margin_pct, 2)
        }
