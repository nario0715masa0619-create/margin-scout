# Phase A1: ローカル本番化シミュレーション チェックリスト

**実施日**: 2026-06-16  
**環境**: Windows PowerShell, ローカル (localhost)

---

## 【1. .env.prod 読み込み】

- [x] .env.prod ファイル作成成功
- [x] EBAY_ENV=live 確認
- [x] LOG_LEVEL=info 確認
- [x] DEBUG=false 確認
- [x] 環境変数適用確認

---

## 【2. Backend 本番相当設定起動】

- [x] venv_backend アクティベート成功
- [x] 環境変数読み込み成功
- [x] python -m uvicorn 起動成功
- [x] コンソール出力: "Application startup complete"
- [x] ポート 8000 バインド確認

---

## 【3. /docs (Swagger UI) 表示確認】

- [x] http://localhost:8000/docs で Swagger UI 表示
- [x] 7 API エンドポイント全表示
  - [x] /api/research/jobs
  - [x] /api/research/jobs/{job_id}
  - [x] /api/research/jobs/{job_id}/results
  - [x] /api/research/jobs/{job_id}/results/{candidate_id}
  - [x] /api/research/jobs/{job_id}/export/csv
  - [x] /api/research/jobs/{job_id}/cancel
  - [x] /api/research/jobs/{job_id}/logs/summary

---

## 【4. Frontend 本番ビルド成功】

- [x] .env.production 作成成功
- [x] npm run build 実行成功 (エラーコード 0)
- [x] ビルド完了メッセージ表示
- [x] 処理時間: 15 秒

---

## 【5. dist/ 生成確認】

- [x] dist/ ディレクトリ作成
- [x] index.html 存在
- [x] assets/ ディレクトリ存在
- [x] assets/app-*.js 存在
- [x] assets/*.css 存在
- [x] 総ファイル数: 12 個

---

## 【6. Frontend ↔ Backend 疎通確認】

- [x] http://localhost:3000 で UI 表示
- [x] ブラウザコンソール 致命的エラーなし
- [x] Network タブ: API リクエスト 200 OK
- [x] CORS エラーなし
- [x] API レスポンス受取可能

---

## 【7. CORS エラー確認】

- [x] CORS エラー表示されない
- [x] ALLOWED_ORIGINS 設定確認
- [x] ブラウザコンソール警告なし

---

## 【8. S01→S05 最小フロー確認】

### S01 リサーチ開始
- [x] キーワード入力可能
- [x] ソース選択可能
- [x] "リサーチ開始" ボタンクリック可能
- [x] ローディング表示

### S02 実行中モニター
- [x] job_id 表示
- [x] ステータス表示
- [x] 進捗バー表示
- [x] 自動遷移 (5-10 秒後)

### S03 候補一覧
- [x] テーブル表示
- [x] Mock データ表示 (10-15 件)
- [x] ソート機能動作
- [x] 複数選択機能動作

### S04 詳細表示
- [x] 詳細ページ表示
- [x] 商品情報表示
- [x] 前/次 ナビゲーション
- [x] UI 崩れなし

### S05 CSV 出力
- [x] CSV ダウンロード可能
- [x] ファイル名形式正確
- [x] ヘッダー行完全
- [x] データ行複数行

---

## 【9. CSV 出力内容確認】

- [x] 出力ファイル名: research_results_YYYYMMDD_HHMMSS.csv
- [x] ヘッダー行: product_name, source_url, price_min, price_max, profit, margin
- [x] データ行数: 15 行
- [x] 内容正確性

---

## 【10. ログファイル出力確認】

- [x] logs/backend.log 作成
- [x] ログレベル区分 (info, warning, error)
- [x] ログ内容正確

---

## 【最終判定】

**全体完了度**: 10 / 10

### 判定
- [x] **GO**: 全項目 ✅ 完了
- [ ] **NO-GO**: 修正必要
- [ ] **条件付き GO**: 軽微な問題のみ

### 修正必要項目
なし

### 備考
すべてのシミュレーション手順において問題なく完了しました。本番相当の環境でも CORS 設定・静的ファイル配信・API 疎通は正常に機能します。

---

## GO 条件（全て満たすこと）
✅ 1-10 全項目チェック完了
✅ S01-S05 最小フロー成功
✅ CSV 出力成功
✅ ログファイル出力

## NO-GO 条件（1 つでも該当したら NO-GO）
(該当なし)
