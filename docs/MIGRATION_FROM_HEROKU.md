# MarginScout Architecture Migration Summary

## 1. 旧 Heroku 前提から新構成への移行サマリー

MarginScout は「サーバーサイドスクレイピング主体（Heroku）」から「**Browser Extension 主体（Vercel/Railway ハイブリッド）**」へとアーキテクチャを完全移行します。

### 構成対比表
| 領域 | 旧構成 | 新構成 |
| :--- | :--- | :--- |
| **Frontend** | Heroku | **Vercel** |
| **Backend API / Worker** | Heroku (Celery + Playwright) | **Railway** (Python) |
| **DB / KVS** | Heroku Postgres / Redis | **Railway Postgres / Upstash Redis** |
| **Main Scraping** | サーバー側 Playwright 常駐実行 | **Browser Extension** (Chrome等) |
| **Fallback Scraping** | なし | **Browserless** |
| **Authentication** | FastAPI JWT | FastAPI JWT (Backendが Bearer Token から user_id 解決) |
| **Product Boundary** | 曖昧になりがちだった | **リサーチ SaaS 領域に厳格に限定** (Sell/在庫管理等はスコープ外) |
| **運用前提** | 24/7 監視体制 | **営業時間内対応ベース** |

### 修正理由
1. **コストと安定性**: Heroku Worker 上で Playwright などのブラウザエンジンを常時稼働させるのは原価が非常に高く、Bot対策に引っかかりやすい。ユーザーのブラウザ（Extension）を主軸とすることで、原価を劇的に下げつつ自然なリクエストとしてスクレイピングを実現する。
2. **スコープの明確化**: 出品（Sell API）や在庫管理などのフルフィルメント領域まで踏み込むとリサーチSaaSとしての強みがボヤけるため、商品マッチングと利益計算に特化する。

---

## 2. Browserless の補完用途定義

Browserless は「メインのスクレイパー」ではなく、**「拡張機能（Extension）では対応できないケースを埋める」ための補完用途** に位置付けます。

- **フォールバック (Fallback)**: Extension側でDOM解析に失敗した場合や、動的トークンの取得が必要な一時的な処理。
- **定期監視 (Monitoring)**: ユーザーのブラウザが閉じている深夜帯などに行う価格変動チェックや新着監視。
- **非対応ソース (Unsupported Sources)**: 拡張機能での操作が技術的に困難、または完全自動化が強く求められる特定の限定的なソース。
- **指標**: Browserless の実行回数や消費時間は「内部原価指標」として集計・監視され、無制限に解放されないようにプランごとに制御される。

---

## 3. 修正対象 Docs 一覧

以下のドキュメントを新方針に沿って修正または作成します。

1. **`docs/SAAS_ARCHITECTURE_OVERVIEW.md`** (全体構成図・責務の変更)
2. **`docs/SAAS_DATABASE_DESIGN.md`** (ResearchJob から capture/import_sessions ベースへの変更)
3. **`docs/SAAS_BILLING_DESIGN.md` / `PRICING_MODEL.md`** (API回数課金からの脱却と指標化)
4. **`docs/SCRAPING_DESIGN.md`** (新設：Extension First & Browserless Fallback)
5. **`docs/API_SPEC.md`** (新設：POST `/api/v1/captures` の採用、user_id排除)
6. **`docs/EXTENSION_SPEC.md`** (新設：拡張機能側の要件定義)
7. **`docs/MIGRATION_FROM_HEROKU.md`** (新設：Herokuからの脱却手順)
8. **`docs/DEPLOYMENT.md`** (`SAAS_HEROKU_DEPLOYMENT.md` の代替)

---

## 4. P0 で直すべき Docs の順序

実装に入る前に、以下の順序でドキュメントの整合性を確立します。

1. **`MIGRATION_FROM_HEROKU.md`**: 今回の決定事項と変更サマリーの恒久的な記録（本書）。
2. **`SAAS_ARCHITECTURE_OVERVIEW.md`**: Extension, SaaS, Browserless の全体構成と責務分担の明記。
3. **`SCRAPING_DESIGN.md`**: Extension 主軸と Browserless 補完の詳細設計。
4. **`API_SPEC.md`**: `POST /api/v1/captures` など、Extension と SaaS 間の通信 I/F 確定。
5. **`SAAS_DATABASE_DESIGN.md`**: API に合わせたデータモデル（`captures`, `import_sessions` 等）の再構築。

---

## 5. Backlog 再編の骨子

### P0 (Docs 修正、API 境界確定、データモデル再整理)
- Docs 全面修正（アーキテクチャ、スクレイピング設計、API設計、データモデル設計）
- Heroku 関連の記述をパージし、Railway/Vercel 前提のデプロイ設計化。
- **残タスク**: `README.md`, `ENV_SETUP.md`, `TESTING_STRATEGY.md` の新構成（Browser Extension First + Railway）への更新。

### P1 (Backend API、認証連携、保存処理)
- Backend での `capture/import` 受信 API の実装。
- Extension から送られてくる Bearer Token を用いた `user_id` 解決とバリデーション。
- PostgreSQL (`source_items`, `ebay_matches` 等) へのデータ永続化処理。

### P2 (Extension MVP、Browserless fallback、Frontend 導線修正)
- Browser Extension の MVP 実装（メルカリ・ヤフオクの DOM 抽出と SaaS への送信）。
- Browserless を用いたフォールバック機能の Celery 統合。
- SaaS Frontend（Vercel）のダッシュボード修正。

### P3 (料金制御、運用改善、監視強化)
- Upstash Redis を用いたプラン別の制限・上限（Rate Limit）コントロール。
- Browserless 原価計測（Telemetry）の組み込み。
- SLA / 運用体制の「営業時間内対応」へのダウングレード対応。
