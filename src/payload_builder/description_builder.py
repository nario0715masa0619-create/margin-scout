"""
Description Builder

ListingReadyRecord から eBay payload の description を生成
"""

from typing import Optional

class DescriptionBuilder:
    """
    description 生成ロジック
    
    user_notes を HTML escape してから description に含める
    """
    
    DESCRIPTION_TEMPLATE = """
{product_name}
{brand} | {model} | {condition}

商品説明：
{user_notes_formatted}

【注意】
本出品は MarginScout により自動生成されました。
ご不明な点はお問い合わせください。
"""

    def build_description(
        self,
        product_name: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        condition: str = "new",
        user_notes: Optional[str] = None
    ) -> tuple[str, list]:
        """
        description を生成
        
        Returns:
            (description, warnings)
        """
        # TODO: Template 適用ロジック実装
        # TODO: HTML escape / sanitize
        # TODO: 長さ制限処理
        raise NotImplementedError("Description builder implementation pending Phase 4")
        
    def sanitize_html(self, text: str) -> str:
        """
        HTML 特殊文字を escape
        """
        # TODO: <, >, &, " などを escape
        raise NotImplementedError("HTML sanitize implementation pending")
