# MarginScout v2.1 UI 設計書

**版：1.0 | 更新日：2026-06-15 | ステータス：Draft**

---

## 📋 目次

1. [概要](#概要)
2. [ユーザーフロー](#ユーザーフロー)
3. [画面設計](#画面設計)
4. [API 仕様](#api-仕様)
5. [状態管理](#状態管理)
6. [エラーハンドリング](#エラーハンドリング)
7. [コンポーネント一覧](#コンポーネント一覧)
8. [UX ガイドライン](#ux-ガイドライン)

---

## 概要

### プロダクト
- **名称**: MarginScout v2.1
- **目的**: 日本国内ソース（Mercari, Yahoo Flea Market, Yahoo Auction, Hardoff）から商品候補を取得し、eBay 参照市場と照合して利益候補を抽出するリサーチツール
- **ターゲット**: 日本発の eBay 出品者
- **主要機能**: リサーチ条件設定 → 実行中モニター → 候補一覧 → 詳細表示 → CSV 出力

### 設計方針
- **フロー**: 5 つの画面を順序立てた操作フロー
- **API**: Backend（FastAPI）との REST API 連携
- **状態管理**: Pinia（Vue 3 の状態管理）
- **エラー対応**: API 失敗時はモーダルまたは通知パネルで表示
- **レスポンシブ**: Desktop 優先（1024px 以上）

---

## ユーザーフロー

### フロー図（テキスト表現）

```
Start
  ↓
[S01] リサーチ条件設定
  • キーワード入力
  • ソース選択（複数可）
  • 日数・最小販売数指定
  ↓ (「リサーチ開始」ボタン)
[API] POST /api/research/jobs
  ↓ (job_id 取得)
[S02] 実行中モニター
  • 進捗バー表示（0～100%）
  • 取得件数・マッチ件数リアルタイム更新
  • ポーリング（2秒間隔）
  ↓ (status: completed)
[S03] 候補一覧
  • テーブル表示（商品名、価格、利益、マッチスコア）
  • 候補選択（チェックボックス）
  • ソート・フィルター機能
  ↓ (候補クリック)
[S04] 候補詳細
  • 価格比較（仕入 vs eBay）
  • 利益計算詳細
  • 前後ナビゲーション
  ↓ (複数選択後)
[S05] CSV 出力
  • 出力オプション選択
  • 列プレビュー表示
  • CSV ダウンロード
  ↓
End
```

### 異常系フロー

```
【API エラー】
  → エラーモーダル表示
  → 再試行ボタン表示
  → ログパネルに詳細記録

【ネットワーク切断】
  → タイムアウト通知
  → 「再接続」ボタン

【ユーザーキャンセル】
  → 「キャンセル」ボタン
  → ジョブ停止 API 呼び出し
  → リサーチ開始画面に戻る
```

---

## 画面設計

### S01: リサーチ条件設定

**目的**: ユーザーが検索条件を入力し、リサーチを開始

#### ワイヤーフレーム

```
┌─────────────────────────────────────┐
│  MarginScout v2.1                   │ ← ナビバー
├─────────────────────────────────────┤
│                                     │
│  📋 リサーチ条件設定                  │
│                                     │
│  キーワード (カンマ区切り)            │
│  [iPhone, Canon, Gucci          ]   │
│                                     │
│  取得元（複数選択可）                 │
│  ☑ Mercari    ☑ Yahoo Flea Market  │
│  ☑ Yahoo Auction  ☑ Hardoff         │
│                                     │
│  取得対象期間（日）: [90      ]      │
│                                     │
│  最小販売数: [2       ]              │
│                                     │
│  [🚀 リサーチ開始]                   │
│                                     │
└─────────────────────────────────────┘
```

#### コンポーネント仕様

| 要素 | タイプ | 初期値 | 必須 | 制約 |
|------|--------|--------|------|------|
| キーワード | テキスト入力 | "" | ✓ | 1～100文字/複数 |
| ソース | チェックボックス | すべて選択 | ✓ | 最大 4 個 |
| 日数 | 数値入力 | 90 | ○ | 1～365 |
| 最小販売数 | 数値入力 | 2 | ○ | 1～1000 |

#### バリデーション

- キーワード空: 「キーワードを入力してください」エラー
- ソース未選択: 「取得元を選択してください」エラー
- 日数範囲外: 「1～365 の値を入力してください」エラー

#### ボタン状態

- 有効: キーワード入力 AND ソース選択
- 無効: 上記条件未満足 (disabled, gray)

---

### S02: 実行中モニター

**目的**: リサーチ進捗をリアルタイム表示

#### ワイヤーフレーム

```
┌─────────────────────────────────────┐
│  MarginScout v2.1                   │
├─────────────────────────────────────┤
│                                     │
│  ⚙️  実行中モニター                   │
│                                     │
│  ジョブID: 550e8400-e29b-41d4-a716  │
│  状態: 実行中                        │
│  進捗: 45%                           │
│                                     │
│  ████████░░░░░░░░░░░ 45%            │
│                                     │
│  取得件数: 20                        │
│  マッチ件数: 12                      │
│                                     │
│  [キャンセル] [候補一覧へ (無効)]     │
│                                     │
│  ℹ️ リサーチを実行中...               │
│                                     │
└─────────────────────────────────────┘
```

#### API ポーリング仕様

- **間隔**: 2 秒
- **エンドポイント**: GET /api/research/jobs/{job_id}
- **停止条件**: status が "completed" または "failed" または "cancelled"
- **タイムアウト**: 30 分（側度ポーリング回数 = 900 回）

#### 進捗バー更新ロジック

```javascript
progress = (matched_items / total_items) * 100
if (progress > 100) progress = 100
if (status === 'completed') progress = 100
```

#### 状態遷移

| 状態 | 表示 | 次アクション |
|------|------|-------------|
| running | "実行中" | ポーリング継続 |
| completed | "完了" | S03 へ自動遷移 |
| failed | "失敗" | エラーモーダル表示 |
| cancelled | "キャンセル済み" | S01 へ戻る |

---

### S03: 候補一覧

**目的**: リサーチ結果を表形式で表示・選択

#### ワイヤーフレーム

```
┌─────────────────────────────────────┐
│  MarginScout v2.1                   │
├─────────────────────────────────────┤
│                                     │
│  📊 候補一覧                          │
│                                     │
│  [検索: ________] [▼利益順] [全選択] [選択解除] │
│                                     │
│  ┌──────────────────────────────┐   │
│  │ ☑ 商品名 | 仕入 | eBay | 利益 │   │
│  ├──────────────────────────────┤   │
│  │ ☑ iPhone16 | ¥80k | $1200 | ✓ │   │
│  │ ☐ Canon EOS | ¥16k | $231 | ✓  │   │
│  │ ☑ Gucci Bag | ¥20k | $468 | ✓  │   │
│  │ ☐ Protector | ¥800 | $48 | ✗  │   │
│  └──────────────────────────────┘   │
│                                     │
│  [CSV出力 (選択3件)]                 │
│                                     │
└─────────────────────────────────────┘
```

#### テーブル列

| 列 | 型 | 幅 | ソート可否 |
|----|----|----|---------|
| 選択 | checkbox | 40px | × |
| 商品名 | link | 250px | ○ |
| 取得元 | text | 120px | ○ |
| 仕入価格 | number | 100px | ○ |
| eBay価格 | number | 100px | ○ |
| 利益 | number | 100px | ○ |
| 利益率 | percent | 80px | ○ |
| スコア | number | 80px | ○ |

#### インタラクション

- **商品名クリック**: S04 詳細表示へ遷移
- **チェック**: Pinia store の selectedCandidates に追加
- **ソート**: 列ヘッダークリック → ASC/DESC 切り替え
- **フィルター**: 検索ボックス → product_name フィルター

#### 色分け規則

| 条件 | 背景色 | テキスト色 |
|------|--------|----------|
| 利益 > 0 | #d4edda | #155724 |
| 利益 < 0 | #f8d7da | #721c24 |
| 行ホバー | #f9f9f9 | - |

---

### S04: 候補詳細

**目的**: 個別候補の詳細情報と比較を表示

#### ワイヤーフレーム

```
┌─────────────────────────────────────┐
│  MarginScout v2.1                   │
├─────────────────────────────────────┤
│                                     │
│  🔍 候補詳細                          │
│                                     │
│  【基本情報】                        │
│  商品名: iPhone 16 Pro Max          │
│  取得元: Mercari                    │
│  条件: Used - Like New              │
│                                     │
│  【価格比較】                        │
│  仕入: ¥80,000 ────→ eBay: $1,200  │
│  (Mercari)              (eBay)      │
│                                     │
│  【利益計算】                        │
│  利益: ¥25,000  | 利益率: 31.25%     │
│  スコア: 0.89   | ステータス: success │
│                                     │
│  【eBay情報】                        │
│  eBay商品: [eBay] iPhone 16 Pro Max │
│  Item ID: 395123456789              │
│                                     │
│  [✓ 選択済み] [◀ 前] [次 ▶] [戻る] │
│                                     │
└─────────────────────────────────────┘
```

#### セクション構成

| セクション | 内容 | 表示方式 |
|----------|------|--------|
| 基本情報 | 商品名、取得元、条件 | キー・バリュー |
| 価格比較 | 仕入 ← → eBay | 矢印付き比較レイアウト |
| 利益計算 | 利益・率・スコア・ステータス | グリッドレイアウト |
| eBay情報 | eBay 商品名・Item ID | キー・バリュー |

#### ナビゲーション

- **前へ**: 一覧の前の候補を表示
- **次へ**: 一覧の次の候補を表示
- **戻る**: S03 一覧に戻る

---

### S05: CSV 出力

**目的**: 選択候補を CSV 形式でダウンロード

#### ワイヤーフレーム

```
┌─────────────────────────────────────┐
│  MarginScout v2.1                   │
├─────────────────────────────────────┤
│                                     │
│  💾 CSV出力                           │
│                                     │
│  出力設定                            │
│  ジョブID: 550e8400-e29b-41d4-a716  │
│  出力件数: 12 件                     │
│                                     │
│  オプション                          │
│  ☑ 利益率を含める                    │
│  ☑ URL を含める                      │
│  ☐ 黒字のみ出力                      │
│                                     │
│  出力列                              │
│  [candidate_id] [product_name]     │
│  [source_channel] [source_price]   │
│  [ebay_price] [profit_jpy]         │
│  [profit_margin_pct] [source_url]  │
│                                     │
│  [📥 CSV ダウンロード] [戻る]        │
│                                     │
│  ✓ 出力成功 (2026-06-15_research.csv) │
│                                     │
└─────────────────────────────────────┘
```

#### CSV 列仕様

```
candidate_id, product_name, source_channel, source_price_jpy,
ebay_title, ebay_price_usd, profit_jpy, profit_margin_pct,
match_score, status, [source_url], [condition_text]
```

#### ファイル名規則

```
research_results_{YYYY-MM-DD}_{HH-mm-ss}.csv

例: research_results_2026-06-15_10-30-45.csv
```

---

## API 仕様

### 1. リサーチ開始

**エンドポイント**: POST /api/research/jobs

**リクエスト**:
```json
{
  "keywords": ["iPhone", "Canon"],
  "sources": ["mercari", "yahoo_flea"],
  "days_back": 90,
  "min_sales": 2
}
```

**レスポンス (200)**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": "2026-06-15T10:30:00Z"
}
```

**エラーレスポンス (400/500)**:
```json
{
  "detail": "keywords is required"
}
```

---

### 2. ジョブ状態取得

**エンドポイント**: GET /api/research/jobs/{job_id}

**レスポンス (200)**:
```json
{
  "job_id": "550e8400-...",
  "status": "running",
  "progress": 45,
  "total_items": 20,
  "matched_items": 12,
  "started_at": "2026-06-15T10:30:00Z",
  "completed_at": null
}
```

---

### 3. 候補一覧取得

**エンドポイント**: GET /api/research/jobs/{job_id}/results?limit=100&offset=0

**レスポンス (200)**:
```json
{
  "job_id": "550e8400-...",
  "total": 12,
  "limit": 100,
  "offset": 0,
  "results": [
    {
      "candidate_id": "RESEARCH-20260615-0001",
      "product_name": "iPhone 16 Pro Max",
      "source_channel": "mercari",
      "source_price": 80000,
      "source_url": "https://jp.mercari.com/item/m123456",
      "condition_text": "Used - Like New",
      "ebay_title": "[eBay] iPhone 16 Pro Max",
      "ebay_price_usd": 1200.50,
      "ebay_item_id": "395123456789",
      "profit_jpy": 25000,
      "profit_margin_pct": 31.25,
      "match_score": 0.89,
      "status": "success"
    }
  ]
}
```

---

### 4. 候補詳細取得

**エンドポイント**: GET /api/research/jobs/{job_id}/results/{candidate_id}

**レスポンス (200)**: 上記と同じ形式の単一オブジェクト

---

### 5. CSV エクスポート

**エンドポイント**: POST /api/research/jobs/{job_id}/export/csv

**リクエスト** (オプション):
```json
{
  "selected_only": true
}
```

**レスポンス (200)**:
```json
{
  "job_id": "550e8400-...",
  "status": "csv_export_prepared",
  "message": "12 items exported",
  "file": "research_results_2026-06-15_10-30-45.csv"
}
```

---

### 6. ジョブキャンセル

**エンドポイント**: POST /api/research/jobs/{job_id}/cancel

**レスポンス (200)**:
```json
{
  "job_id": "550e8400-...",
  "status": "cancelled"
}
```

---

### 7. ログサマリー

**エンドポイント**: GET /api/research/jobs/{job_id}/logs/summary

**レスポンス (200)**:
```json
{
  "job_id": "550e8400-...",
  "total_items": 20,
  "matched_items": 12,
  "error_count": 1,
  "errors": [
    "Hardoff API timeout"
  ]
}
```

---

## 状態管理

### Pinia Store (research.ts)

```typescript
// State
execution_conditions: {
  sources: string[]
  keywords: string[]
  daysBack: number
  minSales: number
}

job_state: {
  jobId: string
  status: 'idle' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number (0-100)
  totalItems: number
  matchedItems: number
  startedAt: string | null
  completedAt: string | null
}

candidates_list: Candidate[]  // S03 で取得

selected_candidates: Set<string>  // S03 で選択

// Actions
setExecutionConditions(conditions)
setJobState(state)
setCandidatesList(candidates)
toggleSelectedCandidate(candidateId)
clearSelection()
```

### ローカルストレージ（オプション）

```
localStorage:
  'research_last_conditions' → execution_conditions
  'research_job_id' → current job_id
```

---

## エラーハンドリング

### エラーカテゴリー

| カテゴリー | 例 | UI 表示 | 再試行 |
|----------|-----|--------|-------|
| ネットワークエラー | タイムアウト、接続失敗 | モーダル + 再試行 | ○ |
| API エラー (4xx) | バリデーション失敗 | インライン通知 | × |
| API エラー (5xx) | サーバー内部エラー | モーダル + 再試行 | ○ |
| ジョブ失敗 | リサーチ中のエラー | ログパネル | × |

### エラーモーダル

```
┌──────────────────────────────┐
│ ⚠️  エラーが発生しました       │
├──────────────────────────────┤
│                              │
│ [詳細] Connection timeout    │
│                              │
│ [再試行] [キャンセル]          │
│                              │
└──────────────────────────────┘
```

### ログパネル（フッター）

```
═══════════════════════════════
📋 実行ログ (3 件の警告)
───────────────────────────────
[E] Mercari API timeout (10:30:15)
[W] Yahoo Flea connection slow (10:30:20)
[I] Research completed (10:32:45)
───────────────────────────────
[詳細ログを表示]
═══════════════════════════════
```

---

## コンポーネント一覧

| コンポーネント | 用途 | 状態 |
|-----------|------|------|
| Navbar | ナビゲーション | ✅ |
| FormInput | テキスト入力 | ✅ |
| Checkbox | チェックボックス | ✅ |
| NumberInput | 数値入力 | ✅ |
| Button | ボタン | ✅ |
| ProgressBar | プログレスバー | ✅ |
| Table | テーブル | ✅ |
| Modal | モーダル | ⏳ |
| Notification | 通知 | ⏳ |
| LogPanel | ログパネル | ⏳ |

---

## UX ガイドライン

### タイポグラフィ

```
見出し (h1): 2rem, bold, #2c3e50
見出し (h2): 1.5rem, bold, #333
本文: 1rem, regular, #333
補助: 0.875rem, regular, #666
```

### カラーパレット

```
Primary: #007bff (青、アクション)
Success: #28a745 (緑、成功・利益)
Warning: #ffc107 (黄、警告)
Danger: #dc3545 (赤、エラー・損失)
Light: #f5f5f5 (背景)
Dark: #2c3e50 (テキスト)
```

### スペーシング

```
xs: 0.25rem (4px)
sm: 0.5rem (8px)
md: 1rem (16px)
lg: 1.5rem (24px)
xl: 2rem (32px)
```

### レスポンシブ

```
モバイル: 320px～767px (未対応)
タブレット: 768px～1023px (未対応)
デスクトップ: 1024px～ (対応)
```

---

## 実装チェックリスト

- [ ] S01: キーワード入力 + ソース選択 + バリデーション
- [ ] S01: API 送信 + job_id 取得
- [ ] S02: ポーリング 2 秒間隔 + 進捗更新
- [ ] S02: ステータス状態遷移（running → completed）
- [ ] S03: テーブル表示 + ソート + フィルター
- [ ] S03: チェックボックス選択 + Pinia 連携
- [ ] S04: 詳細取得 + 表示 + ナビゲーション
- [ ] S05: 出力オプション + CSV ダウンロード
- [ ] エラーモーダル: ネットワークエラー対応
- [ ] ログパネル: ローカルログ記録
- [ ] CORS: Frontend ↔ Backend 通信確認
- [ ] TypeScript: 型チェック OK

---

## 参考資料

- Vue 3 ドキュメント: https://vuejs.org
- Pinia ドキュメント: https://pinia.vuejs.org
- FastAPI ドキュメント: https://fastapi.tiangolo.com
- Material Design: https://material.io
