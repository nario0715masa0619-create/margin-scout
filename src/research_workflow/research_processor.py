"""
MarginScout Research Workflow Processor

このモジュールはリサーチワークフローのメインロジックを実装します。

機能:
- 複数ソースから候補を取得
- 正規化・整理
- ユーザー確認支援
- CSV 出力

詳細ワークフロー: docs/PHASE2_RESEARCH_WORKFLOW.md
"""

from typing import List, Optional
from research_data import ResearchCandidate, SourceType, ResearchStatus


class ResearchWorkflowProcessor:
    """
    リサーチワークフロー処理エンジン
    
    責務:
    - Layer 0 (生データ) → Layer 1 (正規化) → Layer 2 (候補構築)
      → Layer 3 (ユーザー確認) → Layer 4 (CSV 出力)
    """
    
    def __init__(self):
        self.candidates: List[ResearchCandidate] = []
        self.logger = None
    
    def ingest_raw_data(self, raw_data: dict) -> ResearchCandidate:
        raise NotImplementedError("Layer 0 → Layer 1 実装予定")
    
    def build_candidate(self, normalized_data: dict) -> ResearchCandidate:
        raise NotImplementedError("Layer 1 → Layer 2 実装予定")
    
    def filter_candidates(
        self,
        candidates: List[ResearchCandidate],
        filter_criteria: Optional[dict] = None
    ) -> List[ResearchCandidate]:
        raise NotImplementedError("フィルタ機能実装予定")
    
    def add_user_annotation(
        self,
        candidate_id: str,
        notes: Optional[str] = None,
        tags: Optional[List[str]] = None,
        judgement: Optional[str] = None
    ) -> None:
        raise NotImplementedError("ユーザー入力ハンドル実装予定")
    
    def export_to_csv(
        self,
        output_path: str,
        filter_export_ready: bool = True
    ) -> None:
        raise NotImplementedError("CSV エクスポート実装予定")
