"""
CSV Validator

Research CSV のバリデーションロジック
"""

from typing import List, Dict, Tuple
from enum import Enum

class ValidationLevel(str, Enum):
    HARD_ERROR = "hard_error"
    SOFT_WARNING = "soft_warning"
    PENDING_REVIEW = "pending_review"
    SKIP = "skip"

class CSVValidator:
    """
    Research CSV のバリデーション
    """
    
    def __init__(self):
        pass
        
    def validate_row(self, row: Dict) -> Tuple[ValidationLevel, List[str]]:
        """
        単一行のバリデーション
        
        Returns:
            (level, messages) - ValidationLevel と メッセージリスト
        """
        # TODO: 必須フィールド確認ロジック
        # TODO: research_status フィルタ
        # TODO: URL バリデーション
        # TODO: 型チェック
        # TODO: 値域チェック
        raise NotImplementedError("Validator implementation pending Phase 3")
        
    def validate_required_fields(self, row: Dict) -> Tuple[bool, List[str]]:
        """
        必須フィールドチェック
        Hard error の判定に使用
        """
        raise NotImplementedError("Required field validation pending")
        
    def validate_data_types(self, row: Dict) -> Tuple[bool, List[str]]:
        """
        データ型チェック
        """
        raise NotImplementedError("Data type validation pending")
