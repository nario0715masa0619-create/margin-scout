# MarginScout SaaS - アーキテクチャ概要設計書

**バージョン**: 2.0  
**対象範囲**: MarginScout SaaS 化（Browser Extension First Hybrid Architecture）

## ⚠️ スコープ明記 (Product Boundary)

MarginScout は**リサーチ専用 SaaS** であり、以下の機能はシステムの複雑性を排除するため**完全スコープ外 (Out of Scope)** とします。
- Sell API / 出品管理
- 在庫管理 (Inventory)
- 注文管理 (Order Management)
- フルフィルメント (Fulfillment)

---

## 1. 新アーキテクチャの基本方針

### 1.1 Browser Extension First
MarginScout は、フリマサイト（メルカリ・ヤフオク等）からのデータ抽出（スクレイピング）を、サーバーサイドの Bot ではなく、**ユーザーのブラウザ上で動く Chrome 拡張機能 (Browser Extension)** を主軸として実行します。

### 1.2 SaaS Backend の責務限定
SaaS 側のバックエンドサーバーは、スクレイピングの重い処理から解放され、以下の機能に専念します：
- ユーザー認証・認可 (FastAPI JWT)
- サブスクリプション・課金管理 (Stripe) と利用枠 (Quota) 管理
- Extension から受信したデータと eBay Browse API との照合
- 利益計算ロジック・為替レート管理
- リサーチ履歴の PostgreSQL への保存と CSV 出力

### 1.3 Browserless の補完用途
Browserless はメインのスクレイパーとしては使用せず、**Extension では不可能なケースを埋める補完用途** に限定します。
- **定期監視**: ブラウザが閉じている際の価格変動・新着アラート監視。
- **フォールバック**: Extension 側の処理が一時的に失敗した場合のサーバー側リトライ（限定的）。

---

## 2. SaaS 全体アーキテクチャ図

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. Client Side (User Browser)                               │
│                                                             │
│  ┌─────────────────┐       ┌─────────────────────────────┐  │
│  │ SaaS Dashboard  │       │ Browser Extension           │  │
│  │ (Next.js / Vue) │       │ (Content Scripts / Popup)   │  │
│  │ Hosted on Vercel│       │ DOM Parsing & User Actions  │  │
│  └───────┬─────────┘       └─────────────┬───────────────┘  │
└──────────┼───────────────────────────────┼──────────────────┘
           │ HTTPS (Bearer JWT)            │ HTTPS (Bearer JWT)
┌──────────▼───────────────────────────────▼──────────────────┐
│ 2. SaaS Backend (Hosted on Railway)                         │
│                                                             │
│  ┌─────────────────┐       ┌─────────────────────────────┐  │
│  │ FastAPI Server  │───────│ Celery Worker (Python)      │  │
│  │ (Auth/API Core) │       │ (Background Tasks)          │  │
│  └───────┬─────────┘       └─────────────┬───────────────┘  │
│          │                               │                  │
│  ┌───────▼─────────┐       ┌─────────────▼───────────────┐  │
│  │ Railway Postgres│       │ Upstash Redis             │  │
│  │ (DB Storage)    │       │ (Rate Limit / Queue)        │  │
│  └─────────────────┘       └─────────────────────────────┘  │
└──────────────────────────────────────────┬──────────────────┘
                                           │
┌──────────────────────────────────────────▼──────────────────┐
│ 3. External Services & APIs                                 │
│                                                             │
│  ┌─────────────────┐ ┌─────────────────┐ ┌───────────────┐  │
│  │ eBay Browse API │ │ Stripe (Billing)│ │ Browserless   │  │
│  │ (Reference Data)│ │ (Subscriptions) │ │ (Fallback)    │  │
│  └─────────────────┘ └─────────────────┘ └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. データの流れ (Data Flow)

### 3.1 リサーチ実行フロー (Extension 主導)
1. ユーザーが Extension を開き、メルカリ等で検索を実行。
2. Extension の Content Script が画面の DOM を解析し、商品情報（タイトル、価格、URL 等）を抽出。
3. Extension が `POST /api/v1/captures` に抽出データを JSON ペイロードとして送信（HTTP Header に JWT Bearer Token を付与）。
4. SaaS Backend が Token から `user_id` を解決。
5. Backend が eBay Browse API を叩き、抽出データと照合して利益を計算。
6. Backend が PostgreSQL (`captures`, `ebay_matches`) に結果を保存し、Extension にレスポンスを返す。
7. Extension 画面（またはフリマ画面のオーバーレイ）に利益計算結果を表示。

### 3.2 認証・課金フロー
- ユーザーは SaaS Dashboard (Vercel) で会員登録・ログインを行う。
- Stripe Checkout で有料プランを購読する。
- 発行された JWT トークンは Extension 側にも連携され、API リクエスト時に認証情報として利用される。
- Backend (FastAPI) と Upstash Redis によって、月間のリサーチ回数（Quota）上限到達を検知し、API 呼び出しを制限する。

---

## 4. 運用前提

- **営業時間内対応**: Heroku時代の24/7監視体制ではなく、基本的には営業時間内ベストエフォートでのサポートおよび運用保守とします。
- **インフラの可用性**: Vercel と Railway、Upstash の PaaS 標準 SLA に準拠します。
