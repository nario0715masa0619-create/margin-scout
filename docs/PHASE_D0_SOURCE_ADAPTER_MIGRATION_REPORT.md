# Phase D-0: 旧 ERE 資産の棚卸し & 移植計画

**作成日**: 2026-06-15  
**ステータス**: 計画・検証完了  
**対象リポジトリ**: https://github.com/nario0715masa0619-create/ebay-research-edge  

---

## 📋 **Executive Summary**

MarginScout v2.0 の Phase D（仕入れ元スクレイピング）において、旧 eBay Research Edge（ERE）リポジトリに存在する**安定していたスクレイピング処理**を再利用します。

- ✅ **ゼロから書き直さない** → 既存資産を最大限流用
- ✅ **入出力だけ修正** → MarginScout CSV 形式に合わせる
- ✅ **ロジック本体は変更最小** → セレクタ、正規表現、retry ロジックそのまま利用
- ✅ **段階的実装** → Mercari → Yahoo → Hardoff の順で移植

---

## 🔍 **Part 1: 旧 ERE から再利用する関数一覧**

### **1.1 メイン スクレイピング関数**

#### `search_mercari(page, kw, genre="ポケモンカード", is_manual=False)`

**目的**: Mercari から商品検索・スクレイピング

**現在の実装**:
```python
# 入力: Playwright page オブジェクト、キーワードリスト
# 処理:
#   - URL 組み立て: https://jp.mercari.com/search?keyword=...
#   - page.goto() でページ遷移
#   - 'a[href^="/item/m"]' セレクタで商品リンク抽出
#   - innerText から価格を正規表現で抽出: r'¥\s*([\d,]+)'
#   - 除外キーワード判定（"盗難防止" 等）
#   - 最大 5 件まで返却

# 戻り値: list of dict
# [
#   {'price': int, 'title': str, 'url': str, 'image': str, 'site': 'メルカリ'},
#   ...
# ]
```

**そのまま使う部分**:
- CSS セレクタ: `'a[href^="/item/m"]'` ✅
- 価格抽出正規表現: `r'¥\s*([\d,]+)'` ✅
- 除外キーワード: `["盗難防止", "観賞用", "展示用", "レプリカ"]` ✅
- アイテム上限: 5 件 ✅
- 非同期処理フロー: `async/await` ✅

**修正が必要な部分**:
- 戻り値キーをスネークケース統一（`site` → `source_channel`）
- `source_url` に統一（`url` から）
- `source_price` に統一（`price` から）
- eBay 参照価格を合わせるフェーズは 別処理（`ebay_searcher` で実施）

**移植先**: `src/source_adapters/mercari_adapter.py`

#### `search_yahoo(page, kw, genre="ポケモンカード", is_manual=False)`

**目的**: Yahoo フリマ から商品検索・スクレイピング

**現在の実装**:
```python
# 入力: Playwright page オブジェクト、キーワード
# 処理:
#   - URL: https://paypayfleamarket.yahoo.co.jp/search/...
#   - page.goto() でページ遷移
#   - 'a[href*="/item/"]' セレクタで抽出
#   - innerText から価格を正規表現で抽出: r'([\d,]+)\s*円' または r'¥\s*([\d,]+)'
#   - 除外キーワード判定
#   - 最大 5 件まで返却

# 戻り値: list of dict（同 Mercari）
```

**そのまま使う部分**:
- URL パターン ✅
- CSS セレクタ ✅
- 価格抽出ロジック（複数の正規表現フォールバック） ✅
- 除外キーワード ✅
- 最大件数制御 ✅

**修正が必要な部分**:
- 戻り値キー統一（上記 Mercari と同じ）

**移植先**: `src/source_adapters/yahoo_adapter.py`

#### `fetch_yahoo_auction_history(search_query, browser)`

**目的**: Yahoo オークション の落札相場（過去 90 日）を取得

**現在の実装**:
```python
# 入力: 検索クエリ（リスト or 文字列）、Playwright browser オブジェクト
# 処理:
#   - URL: https://auctions.yahoo.co.jp/closedsearch/closedsearch?p=...
#   - ページ読み込み → fontWeightBold クラスから価格抽出
#   - 外れ値除外（上位・下位 10%）
#   - 中央値、最小、最大を計算
#   - 件数と URL も返却

# 戻り値: dict
# {
#     'min': int,
#     'median': int,
#     'max': int,
#     'count': int,
#     'url': str
# }
```

**そのまま使う部分**:
- クラス名セレクタ: `[class*="fontWeightBold"]` ✅
- 外れ値除外ロジック（上位下位 10%） ✅
- 統計計算 ✅

**修正が必要な部分**:
- 戻り値を source_adapters の共通構造に合わせる（新規 dataclass）
- エラーハンドリング統一

**移植先**: `src/source_adapters/yahoo_adapter.py` に統合

#### `search_hardoff(page, kw, genre="ポケモンカード", is_manual=False)`

**目的**: Hardoff ネットモール から商品検索

**現在の実装**:
```python
# 入力: Playwright page、キーワード
# 処理:
#   - URL: https://netmall.hardoff.co.jp/search/?q=...
#   - セレクタで抽出: 'div.item, .product-card, div:has(> a[href*="/product/"])'
#   - innerText から価格抽出：正規表現で数字をマッチ
#   - 除外キーワード判定（config.EXCLUDED_KEYWORDS）
#   - 最大 5 件

# 戻り値: list of dict
```

**そのまま使う部分**:
- セレクタ戦略 ✅
- 価格抽出 ✅
- 除外ロジック ✅

**修正が必要な部分**:
- 戻り値キー統一

**移植先**: `src/source_adapters/hardoff_adapter.py`

### **1.2 ヘルパー関数群**

#### `extract_keywords(title)` → キーワード抽出（ルールベース）
**機能**: 商品名から型番・レアリティ・ポケモン名を抽出

**ロジック**:
- 型番優先（123/456 パターン）
- レアリティ抽出（SAR, SR, AR, HR, UR）
- ポケモン名の日本語マッピング
- フォールバック（3 文字以上の単語抽出）

**そのまま使う**: ✅ ロジック全体

**移植先**: `src/source_adapters/utils/keywords.py`

#### `extract_keywords_ai(title, genre)` → キーワード抽出（AI）
**機能**: OpenAI GPT で日本語キーワード生成

**ロジック**:
- 漢字優先化（例: Isagi Yoichi → 潔世一）
- 日本フリマサイト向け最適化
- プロンプト最適化
- 依存: `OPENAI_API_KEY`

**そのまま使う**: ✅ 関数全体

**修正が必要**: `.env` から API キーを取得する部分（既存 `config_loader.py` で対応可能）

**移植先**: `src/source_adapters/utils/keywords.py`

#### `parse_currency(value)` → 通貨パース
```python
# 入力: pandas Series value（可能性のある型: float, int, str, NaN）
# 処理: 数字以外を削除 → float に変換
# 戻り値: float (失敗時: 0.0)
```
**そのまま使う**: ✅

**移植先**: `src/source_adapters/utils/currency.py`

#### `get_exchange_rate()` → 為替レート取得
```python
# 外部 API: https://api.exchangerate-api.com/v4/latest/USD
# 戻り値: float（JPY レート）
# フォールバック: 157.50 (エラー時)
```
**そのまま使う**: ✅

**修正**: タイムアウト設定を `config_adapters.py` から取得

**移植先**: `src/source_adapters/utils/currency.py`

#### `clean_ebay_id(id_val)` → eBay ID クリーニング
```python
# パターン: v1|123456789|0 → 123456789 に抽出
# フォールバック: 指数表記を通常の整数に修正
```
**そのまま使う**: ✅

**移植先**: `src/source_adapters/utils/currency.py`

### **1.3 設定・定数**
`config_runtime.py` から再利用

| 設定項目 | 説明 | デフォルト |
|---|---|---|
| `MAX_RESEARCH_ITEMS` | 1 回の最大リサーチ件数 | 10 |
| `DEFAULT_SHIPPING_COST_JPY` | 固定送料 | 1500 |
| `FEE_RATES` | ジャンル別eBay手数料率 | `{"default": 0.15}` |
| `BROWSER_GOTO_TIMEOUT_MS` | ページ遷移タイムアウト | 30000 |
| `BROWSER_SELECTOR_TIMEOUT_MS` | 要素待ち時間 | 10000 |
| `BROWSER_SHORT_WAIT_MS` | 短い待機時間 | 1000 |
| `API_REQUEST_TIMEOUT_SECONDS` | API リクエスト タイムアウト | 15 |
| `EXCLUDED_KEYWORDS` | 除外キーワード | `["盗難防止", ...]` |

**そのまま使う**: ✅ 全て

**移植先**: `src/source_adapters/config_adapters.py`

---

## 🏗️ **Part 2: MarginScout 側の配置計画**

### **2.1 新規ディレクトリ構成**
```text
src/source_adapters/
├── __init__.py                           (パッケージ初期化)
├── base_adapter.py                       (基本インターフェース：新規)
├── config_adapters.py                    (設定管理：旧 config_runtime.py 流用)
├── mercari_adapter.py                    (Mercari：旧 search_mercari 移植)
├── yahoo_adapter.py                      (Yahoo フリマ＋オークション：旧 search_yahoo + fetch_yahoo_auction_history 移植)
├── hardoff_adapter.py                    (Hardoff：旧 search_hardoff 移植)
├── common_models.py                      (共通 dataclass：新規)
└── utils/
    ├── __init__.py
    ├── keywords.py                       (旧 extract_keywords, extract_keywords_ai 移植)
    ├── currency.py                       (旧 parse_currency, get_exchange_rate, clean_ebay_id 移植)
    └── playwright_helpers.py             (共通 Playwright ユーティリティ：新規)
```

### **2.2 各 Adapter の構造**

**base_adapter.py (新規)**
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SourceItem:
    """仕入れ元アイテムの共通構造"""
    source_channel: str              # 'メルカリ', 'ヤフーフリマ', 'ハードオフ' 等
    source_url: str
    source_price: int                # JPY
    source_currency: str             # 'JPY'
    condition_text: str              # 新品、未使用、良好 等
    product_title: str
    product_image_url: str
    observed_at: str                 # ISO 8601

class BaseSourceAdapter(ABC):
    """全スクレイピングアダプタの基本クラス"""
    
    @abstractmethod
    async def search(self, keywords: List[str], genre: str) -> List[SourceItem]:
        """キーワードで検索し、アイテムリストを返却"""
        pass
    
    async def close(self):
        """リソース解放（ブラウザクローズ等）"""
        pass
```

**mercari_adapter.py (旧 search_mercari 移植)**
```python
class MercariAdapter(BaseSourceAdapter):
    async def __init__(self, browser):
        self.browser = browser
        self.page = await browser.new_page()
    
    async def search(self, keywords: List[str], genre: str) -> List[SourceItem]:
        # 旧 search_mercari() ロジックを流用
        # 戻り値を SourceItem リストに変換
        pass
    
    async def close(self):
        await self.page.close()
```

### **2.3 common_models.py (新規)**
```python
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class SourceSearchResult:
    """仕入れ元検索結果（複数アダプタから統合）"""
    source_channel: str
    source_url: str
    source_price: int
    source_currency: str
    condition_text: str
    product_title: str
    product_image_url: str
    observed_at: str
    confidence: float = 0.0          # マッチング信頼度（Phase C の product_matcher 結果）

@dataclass
class ResearchCandidateWithSources:
    """eBay 参照価格 + 複数ソースから統合"""
    candidate_id: str
    product_name: str
    ebay_reference_price_usd: float
    ebay_reference_item_id: str
    ebay_reference_url: str
    source_items: List[SourceSearchResult]     # 複数ソースのアイテム
    estimated_profit_usd: float = 0.0
    profit_margin_percent: float = 0.0
    notes: str = ""
```

---

## 🔄 **Part 3: 実行フロー差分**

### 旧 ERE フロー
```text
Flask Webサーバー起動
  ↓
ユーザーがブラウザで http://localhost:5009 にアクセス
  ↓
UI から「リサーチ開始」ボタン → /start-search エンドポイント
  ↓
バックエンドで async main_process() 実行
  ├── eBay API で商品取得
  ├── search_mercari(), search_yahoo(), search_hardoff() 並行実行
  ├── Yahoo オークション履歴取得
  └── 結果をメモリ（RESEARCH_RESULTS）に蓄積
  ↓
UIがポーリング → /data エンドポイントで結果を取得し、ダッシュボード表示
  ↓
ユーザーが「保存」ボタン → Google Sheets へ書き込み
```

### 新 MarginScout フロー（Phase D-1 以降）
```text
CLI: python -m src.research_workflow.cli \
    --category electronics \
    --days 90 \
    --min-sales 2

  ↓
research_processor.py:main()
  ├── EbaySearcher でeBay Browse API から候補検索
  ├── ProductMatcher でスコアリング
  ├── 高スコア候補それぞれに対して:
  │   ├── MercariAdapter.search(keywords)
  │   ├── YahooAdapter.search(keywords)
  │   ├── HardoffAdapter.search(keywords)
  │   └── 結果を統合 → SourceSearchResult[]
  ├── 利益計算（source_price vs ebay_price）
  └── research_results.csv へ書き込み
  ↓
CSV 出力
  ├── research_results.csv
  ├── listing_seed.csv
  └── logs/research_audit_*.jsonl
```

---

## 🔧 **Part 4: 依存ライブラリ差分**

### 旧 ERE の requirements.txt
```text
playwright
requests
pandas
flask
flask-cors
openai
python-dotenv
```

### 新 MarginScout の requirements.txt (既存)
```text
playwright
requests
pandas
python-dotenv
openai
```
**差分**: `-flask, -flask-cors`（CLI モード のため不要）  
**追加不要**: 全て既存で対応可能 ✅

---

## 📊 **Part 5: Phase D-1 実装スケジュール**

| フェーズ | 内容 | 予定日 | 期間 |
|---|---|---|---|
| D-1 | Mercari アダプタ実装＆テスト | 2026-06-15 | 1-2h |
| D-2 | Yahoo アダプタ実装＆テスト | 2026-06-15 | 1-2h |
| D-3 | Hardoff アダプタ実装＆テスト | 2026-06-15 | 1-2h |
| D-4 | e2e テスト（入力 CSV → 全 source 検索 → research_results.csv） | 2026-06-15 | 1h |
| D-5 | エラーハンドリング＆監査ログ統合 | 2026-06-16 | 1h |

---

## ✅ **結論**

- ✅ 旧 ERE から **8 個のメイン関数** を再利用可能
- ✅ ヘルパー関数群（keyword, currency）も全て流用
- ✅ 設定（`config_runtime`）もそのまま適用
- ✅ 新規実装は **基本インターフェース＋ラッパー** のみ
- ✅ ロジック本体の変更は **最小限**
- ✅ 戻り値形式のみ MarginScout CSV 互換に修正
- ✅ 依存ライブラリ追加不要

**推奨: 即座に Phase D-1 実装へ進む**
