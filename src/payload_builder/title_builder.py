"""
Title Builder

ListingReadyRecord から eBay payload の title を生成
"""

from typing import Optional

class TitleBuilder:
    """
    title 生成ロジック
    
    Template A / B / C をサポート
    """
    
    MAX_TITLE_LENGTH = 80
    
    TEMPLATES = {
        "A": "{brand} {product_name} - {condition}",
        "B": "{brand} {model} {product_name} - {condition}",
        "C": "{product_name}",
    }
    
    def __init__(self, template: str = "A"):
        self.template = template
        
    def build_title(
        self,
        product_name: str,
        brand: Optional[str] = None,
        model: Optional[str] = None,
        condition: str = "new"
    ) -> tuple[str, list]:
        """
        title を生成
        
        Returns:
            (title, warnings)
        """
        # TODO: Template 適用ロジック実装
        # TODO: 80文字制限処理
        # TODO: 不要語削除・正規化
        raise NotImplementedError("Title builder implementation pending Phase 4")
