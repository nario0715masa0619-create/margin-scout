# Database Design (PostgreSQL)

## 1. 概要
MarginScout の SaaS バックエンドにおける PostgreSQL のスキーマ設計です。
SaaS としての認証・課金基盤（Users, Subscriptions）と、Browser Extension First アプローチに基づくリサーチドメイン（ImportSessions, SourceItems, EbayMatches）を明確に分離して設計しています。

旧来の単一の `ResearchJob` テーブルは「完全廃止」するのではなく、責務を整理し、取り込み単位・再実行単位・監視単位を管理する `import_sessions` として再定義しました。

## 2. Core (Auth / Billing) スキーマ

### `users`
- `id` (UUID, PK)
- `email` (String, Unique)
- `hashed_password` (String)
- `plan_id` (String) - 例: "free", "basic", "pro"
- `created_at` (DateTime)
- `updated_at` (DateTime)

### `subscriptions`
ユーザーの Stripe 等での決済状態および利用枠 (Quota) を管理します（一部高速な Rate Limit 管理は Upstash Redis でも併用）。
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `stripe_customer_id` (String)
- `stripe_subscription_id` (String)
- `status` (String) - "active", "past_due", "canceled"
- `current_period_end` (DateTime)

---

## 3. Research Domain スキーマ

Browser Extension から送られてくる「画面抽出結果（Captures）」をベースとしたデータモデルです。

### `import_sessions` (旧 ResearchJob)
Extension で 1 回の「検索・抽出」を行った単位、あるいは Browserless で再実行・定期監視を行うジョブ単位を表します。旧 ResearchJob の「リサーチ実行単位の管理」という責務を引き継ぎます。
- `id` (UUID, PK)
- `user_id` (UUID, FK -> users.id)
- `source_domain` (String) - 例: "mercari.com"
- `search_keyword` (String) - ユーザーが検索したキーワード
- `status` (String) - "processing", "completed", "failed"
- `created_at` (DateTime)

### `source_items`
Extension が抽出した個別のフリマ商品データ。
- `id` (UUID, PK)
- `import_session_id` (UUID, FK -> import_sessions.id)
- `user_id` (UUID, FK -> users.id) - RLS (Row Level Security) 用
- `title` (String)
- `url` (String)
- `price_jpy` (Integer)
- `image_url` (String)
- `created_at` (DateTime)

### `ebay_matches`
`source_items` に対して、SaaS Backend が eBay Browse API で引き当てた相場データと利益計算結果。
1つの `source_item` に複数ヒットする可能性があるため 1:N 構造とします。
- `id` (UUID, PK)
- `source_item_id` (UUID, FK -> source_items.id)
- `ebay_item_id` (String)
- `ebay_title` (String)
- `ebay_price_usd` (Float)
- `exchange_rate_jpy` (Float) - 取得時点の為替レート
- `estimated_profit_jpy` (Integer) - 計算された見込み利益
- `match_score` (Float) - タイトル一致度など
- `created_at` (DateTime)

### `profit_snapshots`
後から価格が変動した際などに利益の履歴を追跡・保持するためのスナップショットテーブル（将来拡張用）。
- `id` (UUID, PK)
- `source_item_id` (UUID)
- `ebay_match_id` (UUID)
- `snapshot_date` (DateTime)
- `profit_jpy` (Integer)

---

## 4. マルチテナント対応
- `users` 以外のすべてのテーブルは `user_id` カラムを保持します。
- API レイヤーで JWT から取得した `user_id` を必ず条件（WHERE）に含めることで、テナント間のデータ漏洩を防ぎます。
