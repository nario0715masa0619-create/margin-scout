from typing import List, Dict, Any
from app.schemas.captures import EbayMatchSchema

class EbayMockService:
    @staticmethod
    def mock_match_item(title: str, price_jpy: int) -> List[EbayMatchSchema]:
        """
        Mock implementation of eBay Browse API matching.
        Returns a mock matching result for a given item.
        """
        # Always return a slightly higher price to simulate profit
        # Simple heuristic for mock: assume $1 = 150 JPY, profit = +20%
        usd_price = (price_jpy * 1.2) / 150.0
        profit_jpy = int((usd_price * 150.0) - price_jpy)

        return [
            EbayMatchSchema(
                ebay_title=f"{title} (Mocked from eBay)",
                ebay_price_usd=round(usd_price, 2),
                estimated_profit_jpy=profit_jpy
            )
        ]
