import os
import json
from datetime import datetime

project_path = "C:/NewProjects/margin-scout"
timestamp_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
timestamp_short = datetime.now().strftime("%Y-%m-%d")

# 1. docs/PHASE2_RESEARCH_WORKFLOW.md
workflow_doc = f"""# MarginScout Phase 2: リサーチワークフロー設計

**作成日**: {timestamp_short}  
**プロジェクト**: MarginScout  
**フェーズ**: Phase 2 - リサーチワークフロー設計  
**ステータス**: 設計段階（実装未開始）

---

## 目次

1. [概要](#概要)
2. [リサーチワークフロー全体像](#リサーチワークフロー全体像)
3. [リサーチ責務の定義](#リサーチ責務の定義)
4. [表モード / 裏モードの責務分離](#表モード--裏モードの責務分離)
5. [リサーチ対象データ定義](#リサーチ対象データ定義)
6. [中間データモデル](#中間データモデル)
7. [リサーチ終了点の定義](#リサーチ終了点の定義)
8. [ユーザーフロー](#ユーザーフロー)
9. [データソース責務整理](#データソース責務整理)

---

## 概要

MarginScout のリサーチワークフロー設計は、以下の原則に基づいている。

- **リサーチ起点**: MarginScout は参考価格リサーチツールであり、この機能が中核
- **CSV 中核連携**: リサーチ結果は CSV により次フェーズに連携される
- **責務分離**: リサーチ機能と出品支援機能は明確に分離
- **中間データ重視**: 取得データをいきなり出品データにしない、段階的な整理を重視
- **人機協調**: 自動化できる部分と、ユーザー判断が必要な部分を明確に区別
- **出品実行は別責務**: リサーチ機能は CSV 出力まで、出品実行は別フェーズ

---

## リサーチワークフロー全体像

### ワークフロー図

リサーチ起点（手入力/実店舗/Web観測）
  ↓
Phase 1: データ取得 & 正規化
  ↓
Phase 2: リサーチ候補データ構築
  ↓
Phase 3: ユーザー確認 & 補完
  ↓
Phase 4: CSV 出力対象選定 & 生成
  ↓
CSV → 次フェーズへ引き渡し
  ↓
出品支援ツール（MarginScout または他ツール）へ

---

## リサーチ責務の定義

### MarginScout リサーチ機能が **責任を持つ** こと

1. **参考価格観測** — 複数ソースから参考価格を記録・比較
2. **商品情報抽出** — 商品名、型番、ブランド等の基本情報を抽出
3. **データ正規化** — ソースごとの形式差を吸収し、共通フォーマットに統一
4. **メタデータ記録** — 観測日時、ソース種別、取得元 URL などを保持
5. **候補管理** — 複数の観測を候補として一覧化
6. **ユーザー支援ツール** — 一覧表示、フィルタ、タグ付け、除外機能
7. **CSV 出力** — 確認済み候補を CSV にエクスポート
8. **監査・履歴** — どの候補がいつ、どのソースから収集されたかを記録

### MarginScout リサーチ機能が **責任を持たない** こと

1. ~~出品実行~~ — eBay API への出品は別フェーズ
2. ~~在庫管理~~ — 仕入れ実行後の在庫追跡
3. ~~売上追跡~~ — 出品後の販売結果管理
4. ~~後買いロジック~~ — 販売後の再仕入自動化
5. ~~配送手配~~ — 物流管理
6. ~~決済処理~~ — 支払い・返金管理
7. ~~画像最適化~~ — 画像加工・圧縮は出品フェーズで実施
8. ~~eBay 連携の詳細実装~~ — 出品 API 呼び出しは別責務

---

## 表モード / 裏モードの責務分離

### 設計思想

MarginScout は、以下の2つのモード設定で定義される。

- **表モード**: 一般公開ドキュメント、正式な責務
- **裏モード**: 実装的には存在するが、ドキュメント上は前面に出さない、補助的責務

### 表モードで正式に扱う責務

| 機能 | 説明 | ドキュメント掲載 |
|------|------|-----------------|
| 参考価格リサーチ | eBay、Amazon など複数マーケットプレイスの参考価格を観測 | ✅ README / OPERATION_GUIDE |
| 手入力データ対応 | ユーザーが手作業で入力した候補情報も受け入れ | ✅ CSV_SPEC / 操作ガイド |
| CSV エクスポート | リサーチ結果を CSV 形式で出力 | ✅ 操作ガイド |
| 候補管理 | 複数候補をリスト管理し、フィルタ・タグ付け | ✅ 操作ガイド |
| 基本的な出品支援 CSV 互換性 | 汎用 CSV 形式による出品ツール連携 | ✅ CSV_SPEC |

### 裏モード / 補助扱いとする責務

| 機能 | 説明 | ドキュメント掲載 | 理由 |
|------|------|-----------------|------|
| 実店舗由来オブザーバー | 実際の店舗巡回データを入力し、参考値として記録 | ❌ 最小限 | 法務・サーバー運用の不確実性 |
| 自社リストのスクレイピング | 自社保有データベースからの候補抽出 | ❌ 実装ドキュメント内 | 社内向け、汎用公開対象外 |
| 原価ベース の仕入れ判定支援 | 仕入原価データを参入し、利益率を算出 | △ 計算方式のみ記載 | ビジネスロジック扱い |
| 在庫連動データ | 現在の在庫状況に基づく判定支援 | ❌ 未サポート | 出品フェーズの領域 |

---

## リサーチ対象データ定義

### リサーチ候補レコード（中間データ）が保持すべき項目

#### グループ 1: 基本商品情報

| 項目 | 型 | 必須 | 説明 | 例 |
|------|-----|------|------|-----|
| candidate_id | UUID / 自動採番 | ✅ | リサーチ候補の一意識別子 | ms-res-20260613-0001 |
| product_name | String | ✅ | 商品名（観測ソースから抽出） | Canon EF 50mm f/1.8 STM |
| product_url | String | ✅ | 参考価格観測元の URL | https://www.ebay.com/itm/... |
| source_type | Enum | ✅ | データ取得元の種別 | ebay_listing, manual_input, store_observation |
| sku_candidate | String | ✗ | 商品識別用 SKU（未確定） | CANON-EF50-1.8 |
| brand | String | ✗ | ブランド名 | Canon |
| model_number | String | ✗ | 型番 / モデル | EF50STM |
| category | String | ✗ | 商品カテゴリ | Camera Lenses |

#### グループ 2: 参考価格情報

| 項目 | 型 | 必須 | 説明 | 例 |
|------|-----|------|------|-----|
| reference_price | Decimal | ✅ | 参考価格（単一観測値） | 189.99 |
| currency | String | ✅ | 通貨コード | USD |
| price_low | Decimal | ✗ | 観測価格帯（最低） | 179.99 |
| price_high | Decimal | ✗ | 観測価格帯（最高） | 249.99 |
| price_average | Decimal | ✗ | 複数観測の平均値 | 199.99 |
| condition | Enum | ✗ | 商品状態（参考値） | new, used, refurbished |

#### グループ 3: 観測・メタデータ

| 項目 | 型 | 必須 | 説明 | 例 |
|------|-----|------|------|-----|
| observed_date | DateTime | ✅ | 価格観測日時 | 2026-06-13T14:30:00Z |
| observed_source_url | String | ✅ | 観測元 URL（参考価格取得元） | https://www.ebay.com/itm/... |
| data_source | String | ✅ | どのツール/手段で取得したか | manual, web_scraper, api |
| collection_timestamp | DateTime | ✅ | MarginScout が収集した日時 | 2026-06-13T14:35:00Z |

#### グループ 4: ユーザー補足・判定情報

| 項目 | 型 | 必須 | 説明 | 例 |
|------|-----|------|------|-----|
| user_notes | String | ✗ | ユーザーが手動で記入したメモ | 状態良好、レンズクリア |
| user_tags | List[String] | ✗ | ユーザーが付与したタグ | high-demand, checked |
| judgement_flag | Enum | ✗ | 仕入れ判定の補助フラグ | promising, hold, rejected, needs_review |
| manual_notes_on_value | String | ✗ | 手動での価値判定コメント | 適正価格、仕入れ有望 |

#### グループ 5: 内部管理情報

| 項目 | 型 | 必須 | 説明 | 例 |
|------|-----|------|------|-----|
| research_status | Enum | ✅ | リサーチステータス | draft, under_review, confirmed, excluded |
| csv_export_ready | Boolean | ✅ | CSV 出力対象フラグ | true |
| csv_export_timestamp | DateTime | ✗ | 実際に CSV 出力された日時 | 2026-06-13T15:00:00Z |
| created_at | DateTime | ✅ | リサーチ候補作成日時 | 2026-06-13T14:35:00Z |
| updated_at | DateTime | ✅ | 最終更新日時 | 2026-06-13T14:50:00Z |

---

## 中間データモデル

### データ段階化の考え方

Layer 0: 生データ (Raw Data)
  ↓ Normalize
Layer 1: 正規化データ (Normalized Data)
  ↓ Enrich
Layer 2: リサーチ候補データ (Research Candidate Data)
  ↓ User Review & Tagging
Layer 3: 確認済みリサーチデータ (Confirmed Research Data)
  ↓ Prepare for CSV Export
Layer 4: CSV 出力候補データ (CSV-Ready Data)
  ↓ Export
CSV ファイル (Exported CSV)
  ↓ Next Phase: 出品支援ツール
Layer 5: 出品ペイロードデータ (Listing Payload Data)

---

## リサーチ終了点の定義

### MarginScout リサーチ機能の責務範囲

候補収集 → 正規化 → 確認補完 → CSV 出力 ← ★ ここまで
           │
           ▼
        出品支援ツール（別フェーズ） ← ここから先は別責務

---

## ユーザーフロー

### 標準的なリサーチユーザーフロー

Step 1: リサーチ候補を入力/取得
  ユーザー選択: ① 手入力 CSV でアップロード ② Web スクレイパーから自動取得 ③ 実店舗の紙メモから手入力

Step 2: マージ & 正規化
  MarginScout: ① 複数ソースをマージ ② 形式統一 ③ 重複排除 ④ メタ情報自動抽出

Step 3: 候補一覧で確認
  ユーザー: ブラウザ/CLI で一覧表示確認、フィルタ検索

Step 4: 不要候補を除外
  ユーザー: 一件ずつ/一括で「不要」と mark、理由メモ記入

Step 5: 有望候補にメモ・タグ付与
  ユーザー: メモ追記、タグ付与、判定フラグをセット

Step 6: 最終確認
  ユーザー: 全候補確認、OK なら「CSV 出力」ボタン

Step 7: CSV 出力
  MarginScout: 出力対象をフィルタ、CSV 変換、ファイル生成・保存

Step 8: 次フェーズへ引き渡し
  ユーザー: CSV を出品支援ツールにアップロード、出品フェーズへ進む

---

## データソース責務整理

### データソース分類とサポート体制

#### 正式サポート対象

1. **手入力 CSV**
   - 入力形式: CSV
   - 処理フロー: ユーザー CSV → 正規化 → リサーチ候補 → CSV 出力
   - ドキュメント: CSV_SPEC に詳細記載

2. **eBay リスティング観測**
   - 入力方式: URL 指定または Web スクレイパー自動実行
   - 処理フロー: eBay HTML → パース → 正規化 → リサーチ候補
   - ドキュメント: OPERATION_GUIDE に記載

#### 参考サポート（裏モード）

1. **Amazon リスティング観測**
   - eBay との価格比較に使用
   - 実装ドキュメント内に記載

2. **実店舗観測（手入力メモ）**
   - ユーザーが実店舗で見つけた商品を手で記入
   - 実装ドキュメント内に記載

---

**リビジョン**: 0.1  
**作成日**: {timestamp_full}  
**ステータス**: ドラフト / 設計段階
"""
with open(f"{project_path}/docs/PHASE2_RESEARCH_WORKFLOW.md", "w", encoding="utf-8") as f:
    f.write(workflow_doc)

# 2. docs/RESEARCH_DATA_MODEL.md
data_model_doc = f"""# MarginScout: リサーチデータモデル仕様書

**作成日**: {timestamp_short}  
**バージョン**: 0.1  
**ステータス**: ドラフト / 設計段階

---

## リサーチ候補エンティティ（ResearchCandidate）

### フィールド一覧

- candidate_id: str — 一意識別子
- product_name: str — 商品名
- product_url: str — 参考価格観測元 URL
- source_type: str — ソース種別
- reference_price: Decimal — 参考価格
- currency: str — 通貨コード
- observed_date: datetime — 価格観測日時
- data_source: str — 取得手段
- brand: str (optional) — ブランド名
- model_number: str (optional) — 型番
- category: str (optional) — カテゴリ
- price_low: Decimal (optional) — 価格帯（最低）
- price_high: Decimal (optional) — 価格帯（最高）
- condition: str (optional) — 商品状態
- collection_timestamp: datetime — 収集日時
- user_notes: str (optional) — ユーザーメモ
- user_tags: List[str] — ユーザータグ
- judgement_flag: str (optional) — 判定フラグ
- research_status: str — ステータス
- csv_export_ready: bool — CSV 出力対象フラグ
- created_at: datetime — 作成日時
- updated_at: datetime — 最終更新日時

---

## CSV 出力スキーマ

### CSV ヘッダー定義

```
candidate_id, product_name, reference_price, currency, brand,
model_number, category, product_url, source_type, observed_date,
condition, user_notes, user_tags, judgement_flag, research_status
```

### CSV 出力例

```csv
candidate_id,product_name,reference_price,currency,brand,model_number,category,product_url,source_type,observed_date,condition,user_notes,user_tags,judgement_flag,research_status
ms-res-20260613-0001,Canon EF 50mm f/1.8 STM,189.99,USD,Canon,EF50STM,Camera Lenses,https://www.ebay.com/itm/324901234567,ebay_listing,2026-06-13T14:30:00Z,new,状態良好・レンズクリア,high-demand;checked,promising,confirmed
ms-res-20260613-0002,Nike Air Force 1 US9,110.00,USD,Nike,AF1-US9,Footwear,https://www.ebay.com/itm/324901234568,ebay_listing,2026-06-13T14:35:00Z,new,サイズ確認済み,checked,promising,confirmed
```

---

**改版履歴**:
- v0.1 ({timestamp_short}) — 初版作成
"""
with open(f"{project_path}/docs/RESEARCH_DATA_MODEL.md", "w", encoding="utf-8") as f:
    f.write(data_model_doc)

# 3. examples/research_sample.csv
os.makedirs(f"{project_path}/examples", exist_ok=True)
example_csv = """candidate_id,product_name,reference_price,currency,brand,model_number,category,product_url,source_type,observed_date,condition,user_notes,user_tags,judgement_flag,research_status
ms-res-20260613-0001,Canon EF 50mm f/1.8 STM,189.99,USD,Canon,EF50STM,Camera Lenses,https://www.ebay.com/itm/324901234567,ebay_listing,2026-06-13T14:30:00Z,new,状態良好・レンズクリア,high-demand;checked,promising,confirmed
ms-res-20260613-0002,Nike Air Force 1 US9,110.00,USD,Nike,AF1-US9,Footwear,https://www.ebay.com/itm/324901234568,ebay_listing,2026-06-13T14:35:00Z,new,サイズ確認済み,checked,promising,confirmed
ms-res-20260613-0003,Sony WH-CH510,49.99,USD,Sony,WHCH510,Audio Equipment,https://www.amazon.com/dp/B08GFZV8H3,amazon_listing,2026-06-13T14:40:00Z,new,参考価格として記録,参考,needs_review,under_review
"""
with open(f"{project_path}/examples/research_sample.csv", "w", encoding="utf-8") as f:
    f.write(example_csv)

# 4. src/research_workflow
os.makedirs(f"{project_path}/src/research_workflow", exist_ok=True)
research_data_py = '''"""
MarginScout Research Data Models

このモジュールは、リサーチワークフローで使用されるデータモデルを定義します。

設計ドキュメント: docs/RESEARCH_DATA_MODEL.md
詳細ワークフロー: docs/PHASE2_RESEARCH_WORKFLOW.md
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class SourceType(str, Enum):
    EBAY_LISTING = "ebay_listing"
    AMAZON_LISTING = "amazon_listing"
    MANUAL_INPUT = "manual_input"
    STORE_OBSERVATION = "store_observation"


class DataSourceMethod(str, Enum):
    WEB_SCRAPER = "web_scraper"
    MANUAL = "manual"
    API = "api"
    OCR = "ocr"


class ResearchStatus(str, Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    CONFIRMED = "confirmed"
    EXCLUDED = "excluded"


class JudgementFlag(str, Enum):
    PROMISING = "promising"
    HOLD = "hold"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"


class Condition(str, Enum):
    NEW = "new"
    USED = "used"
    REFURBISHED = "refurbished"
    UNKNOWN = "unknown"


@dataclass
class ResearchCandidate:
    """
    リサーチ候補エンティティ
    
    参考価格リサーチから得られた商品候補を表現する。
    出品用の最終形ではなく、仕入れ判定や候補整理に用いる
    中間データ構造。
    """
    
    candidate_id: str
    product_name: str
    product_url: str
    source_type: SourceType
    reference_price: Decimal
    currency: str
    observed_date: datetime
    data_source: DataSourceMethod
    
    brand: Optional[str] = None
    model_number: Optional[str] = None
    category: Optional[str] = None
    
    price_low: Optional[Decimal] = None
    price_high: Optional[Decimal] = None
    condition: Optional[Condition] = None
    
    collection_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    user_notes: Optional[str] = None
    user_tags: List[str] = field(default_factory=list)
    judgement_flag: Optional[JudgementFlag] = None
    
    research_status: ResearchStatus = ResearchStatus.DRAFT
    csv_export_ready: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            'candidate_id': self.candidate_id,
            'product_name': self.product_name,
            'reference_price': str(self.reference_price),
            'currency': self.currency,
            'brand': self.brand or '',
            'model_number': self.model_number or '',
            'category': self.category or '',
            'product_url': self.product_url,
            'source_type': self.source_type.value,
            'observed_date': self.observed_date.isoformat(),
            'condition': self.condition.value if self.condition else '',
            'user_notes': self.user_notes or '',
            'user_tags': ';'.join(self.user_tags) if self.user_tags else '',
            'judgement_flag': self.judgement_flag.value if self.judgement_flag else '',
            'research_status': self.research_status.value,
        }
    
    def mark_for_export(self) -> None:
        self.csv_export_ready = True
        self.updated_at = datetime.utcnow()
    
    def exclude(self) -> None:
        self.research_status = ResearchStatus.EXCLUDED
        self.csv_export_ready = False
        self.updated_at = datetime.utcnow()
'''
with open(f"{project_path}/src/research_workflow/research_data.py", "w", encoding="utf-8") as f:
    f.write(research_data_py)

research_processor_py = '''"""
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
'''
with open(f"{project_path}/src/research_workflow/research_processor.py", "w", encoding="utf-8") as f:
    f.write(research_processor_py)

init_py = '''"""
MarginScout Research Workflow Package

リサーチワークフロー関連モジュールのパッケージ。
"""

from .research_data import (
    ResearchCandidate,
    SourceType,
    DataSourceMethod,
    ResearchStatus,
    JudgementFlag,
    Condition,
)
from .research_processor import ResearchWorkflowProcessor

__all__ = [
    'ResearchCandidate',
    'SourceType',
    'DataSourceMethod',
    'ResearchStatus',
    'JudgementFlag',
    'Condition',
    'ResearchWorkflowProcessor',
]
'''
with open(f"{project_path}/src/research_workflow/__init__.py", "w", encoding="utf-8") as f:
    f.write(init_py)

# 5. PHASE2_COMPLETION_REPORT.json
phase2_report = {
    "timestamp": timestamp_full,
    "phase": "Phase 2: Research Workflow Design",
    "status": "COMPLETED",
    "documents_created": [
        "docs/PHASE2_RESEARCH_WORKFLOW.md",
        "docs/RESEARCH_DATA_MODEL.md",
        "examples/research_sample.csv",
        "src/research_workflow/research_data.py",
        "src/research_workflow/research_processor.py",
        "src/research_workflow/__init__.py"
    ],
    "key_findings": {
        "research_responsibility": "Data collection → Normalization → User confirmation → CSV export",
        "workflow_layers": {
            "layer_0": "Raw Data (multiple formats)",
            "layer_1": "Normalized Data (unified schema)",
            "layer_2": "Research Candidate (with metadata)",
            "layer_3": "Confirmed Research Data (user annotated)",
            "layer_4": "CSV-ready Data"
        },
        "mode_separation": {
            "published_modes": ["Manual CSV input", "eBay listing observation"],
            "reference_modes": ["Amazon listing observation", "Store observation"]
        },
        "data_model_fields": [
            "candidate_id", "product_name", "reference_price", "currency", "brand",
            "model_number", "category", "product_url", "source_type", "observed_date",
            "condition", "user_notes", "user_tags", "judgement_flag", "research_status"
        ]
    },
    "design_principles": [
        "Research-first: MarginScout is fundamentally a research tool",
        "CSV as core connector: CSV is the primary interchange format",
        "Responsibility separation: Research and listing support are distinct",
        "Intermediate data focus: Do not rush raw data to listing format",
        "User-machine collaboration: Clear distinction of human judgment vs. automation"
    ],
    "next_phase": "Phase 3: CSV Data Integration Design"
}

with open(f"{project_path}/PHASE2_COMPLETION_REPORT.json", "w", encoding="utf-8") as f:
    json.dump(phase2_report, f, indent=4, ensure_ascii=False)

# 6. Update README.md
readme_update = f"""

---

## 📋 Phase 2: リサーチワークフロー設計 (完了)

**ステータス**: 設計完了  
**完了日**: {timestamp_short}

### 成果物

✅ docs/PHASE2_RESEARCH_WORKFLOW.md — リサーチワークフロー詳細設計  
✅ docs/RESEARCH_DATA_MODEL.md — リサーチデータモデル仕様  
✅ examples/research_sample.csv — サンプル CSV（リサーチ候補）  
✅ src/research_workflow/ — Python skeleton (research_data.py, research_processor.py)  

### 設計要点

**リサーチ責務**: データ収集 → 正規化 → ユーザー確認 → CSV 出力

**中間データ層 (Layer 構造)**:
- Layer 0: 生データ (Raw Data)
- Layer 1: 正規化データ (Normalized Data)
- Layer 2: リサーチ候補 (Research Candidate Data)
- Layer 3: 確認済みデータ (Confirmed Research Data)
- Layer 4: CSV 出力候補 (CSV-Ready Data)

**表モード / 裏モード分離**:
- 表: 手入力 CSV、eBay リスティング観測（公式ドキュメント記載）
- 裏: Amazon 観測、実店舗メモ（実装時のみ言及）

**リサーチ終了点**: CSV 出力まで（出品実行は別フェーズ）

---
"""

if os.path.exists(f"{project_path}/README.md"):
    with open(f"{project_path}/README.md", "a", encoding="utf-8") as f:
        f.write(readme_update)
