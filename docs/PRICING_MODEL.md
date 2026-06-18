# Pricing Model & Quota Design

## 1. 概要
MarginScout SaaS の料金モデルと、システム内での利用上限（Quota）管理の設計方針です。

## 2. 料金モデル前提
- **無制限 (Unlimited) は提供しない**
  - バックエンドでの eBay API 呼び出しや、Browserless 経由のフォールバック・監視には原価がかかるため、原価割れを防ぐためにすべてのプランで上限を設けます。
- **表面上の「API回数課金」の隠蔽**
  - エンドユーザーには API の概念を直接意識させず、「リサーチ実行回数」「保存検索数」「履歴保存期間」などのビジネス価値ベースの指標を提供します。

## 3. プラン別の制限指標 (例)

| 機能 / 指標 | Free / Trial | Basic | Pro |
| :--- | :--- | :--- | :--- |
| **月間リサーチ（Import）回数** | 100 回 | 1,000 回 | 5,000 回 |
| **自動監視ジョブ（Browserless）**| 0 件 | 5 件 | 20 件 |
| **履歴保存期間** | 7 日 | 30 日 | 無制限 |
| **CSV エクスポート機能** | 不可 | 可能 | 可能 |
| **同時実行数制限 (Concurrency)**| 1 | 3 | 10 |

## 4. 制限（Rate Limit & Quota）の実装方針

- **Upstash Redis の活用**
  - Redis を用いてユーザー単位の `monthly_captures:{user_id}:{YYYY-MM}` カウンタをインクリメントします。
  - FastAPI 側の Middleware または Dependency 注入で、API 呼び出しの直前に上限（Limit）に達していないかチェックします。
- **Browserless の原価管理 (Telemetry)**
  - Browserless 経由での監視タスクやフォールバックが走った場合、実行秒数（またはセッション回数）を内部的な原価メトリクスとして PostgreSQL に記録し、プラン設計の分析に活用します（ユーザーには見せません）。
- **制限超過時のハンドリング**
  - Extension 側で `429 Too Many Requests` または `403 Forbidden` を受け取った場合、「今月のリサーチ上限に達しました。プランをアップグレードしてください。」という通知（Stripe Checkout へのリンク）を表示します。
