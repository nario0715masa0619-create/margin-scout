# P3 Contract: Staging 環境での新構成検証

## 目的

Vercel + Railway + Upstash + Browserless の新インフラで、Extension → Backend → Monitoring → Browserless フォールバック → Frontend の全フロー動作を検証するための契約書。

**スコープ**: Staging 環境での検証のみ。Production Deploy は次フェーズ。

---

## 1. SavedSearch（保存検索・監視ジョブ）

### 1.1 概要

ユーザーが検索条件を「保存検索」として登録し、定期的に自動取得（監視）できる機能。

### 1.2 データモデル

| フィールド | 型 | 説明 | 例 |
|---|---|---|---|
| `id` | UUID | 主キー | `550e8400-...` |
| `user_id` | UUID | 所有者 | ユーザー ID |
| `name` | String(256) | 検索名 | `"iPhone 14 新品"` |
| `source` | String(50) | 取得元 | `"mercari"`, `"yahoo_auction"`, `"yahoo_flea"` |
| `filters` | JSON | 検索条件（詳細後述） | `{ keyword, options, conditions, ... }` |
| `is_monitoring_enabled` | Boolean | 監視有効化 | `true` / `false` |
| `monitoring_interval_hours` | Integer | 監視間隔 | `24`（1日）, `12`, `6` 等 |
| `next_run_at` | DateTime | 次実行予定時刻 | `2026-06-18T10:00:00Z` |
| `last_run_at` | DateTime | 最終実行日時 | `2026-06-17T10:00:00Z` |
| `last_run_status` | String(50) | 最終実行結果 | `"pending"`, `"success"`, `"failed"` |
| `last_run_error` | String(512) | エラー詳細 | `"Browserless timeout"` |
| `created_at` | DateTime | 作成日時 | `2026-06-01T15:30:00Z` |
| `updated_at` | DateTime | 更新日時 | `2026-06-17T10:00:00Z` |

### 1.3 Filters JSON スキーマ

SavedSearch の `filters` フィールドは以下の構造を持つ JSON：

```json
{
  "keyword": "iPhone 14 Pro",
  "options": {
    "on_sale": true,
    "fixed_price": false,
    "auction": true
  },
  "conditions": ["new", "almost_new"],
  "price_range": {
    "min": 50000,
    "max": 150000
  },
  "sort": "profit_desc",
  "exclude_keywords": ["fake", "replica", "used parts", "parts only"]
}
```

Filters フィールド詳細:

キー	型	必須	説明
keyword	string	✅	検索キーワード（例: "iPhone 14"）
options	object		取得元固有のオプション（Mercari: on_sale, fixed_price; Yahoo: auction等）
conditions	array[string]		商品状態（"new", "almost_new", "good", "fair", "used"）
price_range	object		{ min, max } 価格範囲（円）
sort	string		ソート順（"date_desc", "profit_desc", "margin_desc"）
exclude_keywords	array[string]		除外キーワード（マッチしたら商品をスキップ）

### 1.4 ImportSession との関連
- SavedSearch から手動「再取得」または監視で実行 → ImportSession が作成される
- ImportSession テーブルに `saved_search_id` FK を追加
- Extension からの直接キャプチャは `saved_search_id = NULL`

## 2. Browserless Orchestrator（スクレイピング統合）
### 2.1 概要
Browserless API を通じたスクレイピングを抽象化し、3 つのユースケースに対応：
- ExtensionFallback: Extension が DOM 取得失敗時のサーバー側補完
- ManualRerun: ユーザーが保存検索から「再取得」ボタンをクリック
- MonitoringProvider: 監視ジョブが定期実行

### 2.2 責務分離
```
BrowserlessOrchestrator
├── ExtensionFallback Provider
│   ├── 呼び出し元: Extension が 429 / Timeout で失敗
│   ├── 処理: Browserless で Mercari / Yahoo をスクレイピング
│   └── 結果: ImportSession・SourceItem・EbayMatch・ProfitSnapshot 作成
│
├── ManualRerun Provider
│   ├── 呼び出し元: Dashboard から POST /api/v1/saved-searches/{id}/rerun
│   ├── 処理: 指定 SavedSearch の filters で Browserless 実行
│   └── 結果: ImportSession・SourceItem・EbayMatch・ProfitSnapshot 作成
│
└── MonitoringProvider
    ├── 呼び出し元: Monitoring Dispatcher が next_run_at 条件でトリガー
    ├── 処理: Browserless で Mercari / Yahoo をスクレイピング
    └── 結果: ImportSession・SourceItem・EbayMatch・ProfitSnapshot 作成
```

### 2.3 インターフェース
```python
# 基本インターフェース
class FallbackProvider(ABC):
    async def scrape(
        self,
        source: str,           # "mercari", "yahoo_auction", "yahoo_flea"
        filters: dict          # Filters JSON スキーマ（1.3 参照）
    ) -> List[Dict]:
        """
        フリマをスクレイピング
        
        Returns: [
            {
                "title": "iPhone 14 Pro",
                "price_jpy": 95000,
                "url": "https://mercari.jp/item/m123",
                "image_url": "...",
                "seller_name": "User123",
                "condition": "new",
                "category": "smartphones",
                "fetched_at": "2026-06-17T10:30:00Z"
            },
            ...
        ]
        """
        pass

# Orchestrator インターフェース
class BrowserlessOrchestrator:
    def __init__(self):
        self.providers = {
            "mercari": MercariProvider(),
            "yahoo_auction": YahooAuctionProvider(),
            "yahoo_flea": YahooFleaProvider(),
        }
    
    async def capture_with_fallback(
        self,
        source: str,
        filters: dict,
        fallback_reason: str  # "extension_failure", "manual_rerun", "monitoring"
    ) -> Dict:
        """
        スクレイピング実行（リトライ・ログ記録含む）
        
        Returns: {
            "success": bool,
            "items": [
                { title, price_jpy, url, ... }
            ],
            "fallback_reason": str,
            "error": str (if failed),
            "retry_count": int,
            "duration_ms": int
        }
        """
        pass
```

### 2.4 エラーハンドリング
| エラー | 対応 |
|---|---|
| Browserless Timeout | リトライ 3 回（指数バックオフ: 2s, 4s, 8s） |
| Rate Limit (429) | キュー遅延、最大 5 分まで待機 |
| DOM Selector Not Found | ログ記録、空配列を返す（エラーとして扱わない） |
| Authentication Error | 管理者アラート、タスク停止 |

### 2.5 ログ・監視
全スクレイピング試行を UsageLog に記録：
```python
UsageLog(
    user_id=user_id,
    source="mercari",
    fallback_provider="browserless",
    success=True,
    item_count=8,
    cost_estimate=50.0,  # 推定 ¥50（テスト）
)
```

## 3. Monitoring（定期実行）
### 3.1 概要
SavedSearch の `is_monitoring_enabled=true` かつ `next_run_at <= now()` の全件を自動実行。

### 3.2 Dispatcher パターン
```
Celery Beat
  ↓ (毎 5 分)
dispatch_due_monitoring_jobs()  ← Dispatcher タスク
  ↓
  SELECT * FROM saved_searches
  WHERE is_monitoring_enabled=true
  AND next_run_at <= now()
  AND user_id NOT IN (rate-limit-exceeded-users)
  ↓
  FOR EACH saved_search:
    execute_saved_search_job.delay(saved_search_id)
```

### 3.3 実行フロー
Dispatcher (毎 5 分実行):
- `next_run_at <= now()` の SavedSearch を検索
- Rate Limit に達していないユーザーのみ対象
- `execute_saved_search_job` タスクを Dispatch

Worker (`execute_saved_search_job`):
- SavedSearch 詳細を取得
- Browserless Orchestrator を呼び出し
- ImportSession・SourceItem・EbayMatch・ProfitSnapshot を作成
- last_run_at, last_run_status, next_run_at を更新
- `next_run_at = now() + monitoring_interval_hours`

### 3.4 Celery Beat スケジュール
```python
app.conf.beat_schedule = {
    'dispatch-monitoring-jobs': {
        'task': 'app.tasks.monitoring.dispatch_due_monitoring_jobs',
        'schedule': crontab(minute='*/5'),  # 毎 5 分実行
        'options': { 'expires': 240 }
    },
}
```

### 3.5 ステータス遷移
```
created (next_run_at = now + 24h)
  ↓
next_run_at に達した
  ↓
dispatch_due_monitoring_jobs で拾い出す
  ↓
execute_saved_search_job 実行
  ├─ success → last_run_status="success", next_run_at = now + 24h
  └─ failed → last_run_status="failed", last_run_error="...", next_run_at = now + 1h (retry)
```

## 4. Usage Logging（利用追跡）
### 4.1 概要
API 利用（Extension キャプチャ、Browserless 呼び出し等）を追跡し、課金・Rate Limit 管理に利用。

### 4.2 ログモデル
| フィールド | 型 | 説明 |
|---|---|---|
| id | UUID | 主キー |
| user_id | UUID | ユーザー |
| source | String(50) | 取得元（"extension", "manual_rerun", "monitoring"） |
| fallback_provider | String(50) | フォールバック先（"browserless", "http_api"） |
| success | Boolean | 成功/失敗 |
| item_count | Integer | 取得件数 |
| cost_estimate | Float | 推定コスト（¥） |
| created_at | DateTime | 記録日時 |

### 4.3 月間集計 API
```http
GET /api/v1/usage/monthly

Returns:
{
  "month": "2026-06",
  "extension_captures": 100,
  "manual_reruns": 5,
  "monitoring_runs": 30,
  "total_browserless_calls": 35,
  "total_items_captured": 5000,
  "estimated_cost_jpy": 15000,
  "rate_limit_remaining": 965
}
```

## 5. 実装スケジュール
| フェーズ | 内容 | 所要時間 |
|---|---|---|
| P3-1a | SavedSearch + UsageLog モデル実装 | 2-3 h |
| P3-1d | SavedSearch CRUD + Rerun API | 3-4 h |
| P3-1b | Browserless Orchestrator 実装 | 3-4 h |
| P3-1c | Monitoring Dispatcher + Worker | 2-3 h |
| pytest | 全テスト実行 | 1-2 h |
| P3-2a-c | Staging インフラ構築 | 2-3 h |
| P3-2e | Staging E2E テスト | 2-3 h |
| P3-1e | SavedSearch UI 実装 | 3-4 h |
| P3-2d | Chrome Web Store 登録準備 | 1-2 h |

## 承認
本契約に基づき、以下を実装：
- SavedSearch モデル（1.2）
- UsageLog モデル（4.2）
- Browserless Orchestrator 設計（2.2-2.5）
- Monitoring Dispatcher 設計（3.2-3.5）
