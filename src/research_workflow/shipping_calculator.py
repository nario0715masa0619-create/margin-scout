"""
Shipping Calculator - FedEx と日本郵政 EMS を対応

送料計算エンジン for MarginScout
実際のカテゴリ・重さに基づいて正確な送料を計算
"""

class ShippingCalculator:
    """国際送料計算"""
    
    # 日本郵政 EMS - USA（Fourth Zone）レート表 (JPY)
    # https://www.post.japanpost.jp/send/oversea/charge/list-ems/all_en.html
    JAPAN_POST_EMS_RATES_JPY = {
        500: 3900,      # Up to 500g
        600: 4180,      # Up to 600g
        700: 4460,
        800: 4740,
        900: 5020,
        1000: 5300,     # 1kg
        1250: 5990,
        1500: 6600,
        1750: 7290,
        2000: 7900,     # 2kg
        2500: 9100,
        3000: 10300,    # 3kg
        3500: 11500,
        4000: 12700,
        4500: 13900,
        5000: 15100,    # 5kg
        6000: 17500,
        7000: 19900,
        10000: 27100,   # 10kg
        15000: 39100,   # 15kg
        20000: 51100,   # 20kg
        30000: 75100,   # 30kg (max)
    }
    
    # FedEx International Economy - Japan to USA (概算)
    # https://www.fedex.com/en-jp/shipping/services/international-economy.html
    FEDEX_INTL_ECONOMY_USD = {
        # weight (lbs) -> USD
        1: 35,      # 1 lb
        2: 38,
        3: 40,
        5: 45,
        10: 60,
        15: 75,
        20: 90,
        30: 120,
    }
    
    # カテゴリ別の平均重さ推定値 (グラム)
    CATEGORY_WEIGHTS_G = {
        "electronics": 500,      # スマートフォン、小型電子機器
        "camera": 1000,          # デジカメ、レンズ
        "games": 300,            # ゲーム、グッズ
        "fashion": 200,          # 衣類、アクセサリ
        "hobby": 400,            # コレクタブル、フィギュア
        "default": 500
    }
    
    def __init__(self, exchange_rate: float = 157.50):
        self.exchange_rate = exchange_rate
    
    def get_nearest_weight_bracket(self, weight_grams: int, rate_table: dict) -> int:
        """重さに基づいて最適なレートテーブル行を取得"""
        for bracket in sorted(rate_table.keys()):
            if weight_grams <= bracket:
                return bracket
        return max(rate_table.keys())
    
    def calculate_japan_post_ems_jpy(self, weight_grams: int) -> dict:
        """日本郵政 EMS の送料を計算（JPY）"""
        bracket = self.get_nearest_weight_bracket(weight_grams, self.JAPAN_POST_EMS_RATES_JPY)
        shipping_jpy = self.JAPAN_POST_EMS_RATES_JPY[bracket]
        
        return {
            "carrier": "Japan Post EMS",
            "weight_g": weight_grams,
            "weight_bracket_g": bracket,
            "shipping_jpy": shipping_jpy,
            "shipping_usd": round(shipping_jpy / self.exchange_rate, 2),
            "estimated_days": "3-5"
        }
    
    def calculate_fedex_intl_economy_usd(self, weight_lbs: float) -> dict:
        """FedEx International Economy の送料を計算（USD）"""
        # ポンドを整数に丸める
        weight_bracket = int(weight_lbs)
        if weight_bracket < 1:
            weight_bracket = 1
        
        # 最適なレート行を取得
        bracket = self.get_nearest_weight_bracket(weight_bracket, self.FEDEX_INTL_ECONOMY_USD)
        shipping_usd = self.FEDEX_INTL_ECONOMY_USD[bracket]
        
        return {
            "carrier": "FedEx International Economy",
            "weight_lbs": weight_lbs,
            "weight_bracket_lbs": bracket,
            "shipping_usd": shipping_usd,
            "shipping_jpy": round(shipping_usd * self.exchange_rate, 0),
            "estimated_days": "5-7"
        }
    
    def estimate_weight_from_category(self, category: str) -> int:
        """カテゴリから平均重さを推定"""
        return self.CATEGORY_WEIGHTS_G.get(category.lower(), self.CATEGORY_WEIGHTS_G["default"])
    
    def recommend_carrier(self, weight_grams: int) -> str:
        """重さに基づいてキャリアを推奨"""
        # 日本郵政 EMS は軽量向け、FedEx は重量向け
        if weight_grams <= 2000:  # 2kg 以下
            return "Japan Post EMS"
        else:
            return "FedEx International Economy"
    
    def get_optimal_shipping(self, weight_grams: int, carrier: str = None) -> dict:
        """最適な送料を取得"""
        if carrier is None:
            carrier = self.recommend_carrier(weight_grams)
        
        if carrier == "Japan Post EMS":
            return self.calculate_japan_post_ems_jpy(weight_grams)
        elif carrier == "FedEx International Economy":
            weight_lbs = weight_grams / 453.592  # グラム → ポンド
            return self.calculate_fedex_intl_economy_usd(weight_lbs)
        else:
            raise ValueError(f"Unknown carrier: {carrier}")
