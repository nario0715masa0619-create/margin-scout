# Scraping Execution Design

## 1. 概要

本ドキュメントは MarginScout における外部サイト（フリマサイト等）からのデータ取得（スクレイピング）戦略を定義します。
MarginScout は SaaS のサーバーインフラに対する過度な負荷や Bot 対策による遮断リスクを最小化するため、**Browser Extension First** (拡張機能主軸) アプローチを採用し、**Browserless** を補完的なフォールバック用途に制限します。

## 2. 責務分担とアーキテクチャ

### 2.1 Browser Extension (主軸)
- **対象ソース**: メルカリ、Yahoo!フリマ、ヤフオク等、Bot対策が厳格で、DOMアクセスが必要な主要なフリマサイト。
- **実行環境**: ユーザーの PC ローカル（Chrome ブラウザ上）。
- **役割**:
  - ユーザーがフリマサイトで検索・閲覧した際、Content Script が画面の DOM を解析。
  - タイトル、価格、画像URL、商品リンク等を抽出。
  - 抽出したデータを JSON 化し、SaaS Backend API (`POST /api/v1/captures`) へ送信。
- **メリット**:
  - ユーザーの正規のブラウザセッション（IP、クッキー、User-Agent）を利用するため、CAPTCHA に引っかかりにくい。
  - サーバー側でのブラウザ実行コスト（原価）が実質ゼロ。

### 2.2 SaaS Backend (データ処理)
- **対象ソース**: eBay Browse API 等、公式 API が提供されているもの、またはサーバーからの単純な HTTP GET で完結するもの。
- **実行環境**: Railway (FastAPI / Celery)
- **役割**:
  - Extension から送られてきた Payload を受け取る。
  - eBay API にリクエストを送り、相場価格を取得。
  - 利益率を計算し、結果を DB に保存・Extension に返却。

### 2.3 Browserless (補完/フォールバック)
- **対象**: Extension が対応できない高度な自動化、または定期監視。
- **実行環境**: Browserless.io (Worker から WebSocket で接続)
- **役割**:
  - **Fallback**: Extension での DOM パースに失敗し、バックグラウンドでの再試行が必要な場合。
  - **Monitoring**: ユーザーのブラウザが閉じている夜間に、設定されたキーワードで定期的に新着アイテムを監視する場合。
- **制約**: 内部原価が発生するため、ユーザープラン（利用枠）に応じて実行回数が厳密にコントロールされる。

---

## 3. 実装上の注意点

### 3.1 Extension からの Payload 送信
Extension は SaaS に対して以下のフォーマットでデータを送信します（API仕様は `API_SPEC.md` を参照）。
送信時に `user_id` は含めず、認証トークン (Bearer JWT) から Backend が解決します。

```json
{
  "source_domain": "mercari.com",
  "search_keyword": "Pokemon Card",
  "items": [
    {
      "title": "Pikachu Promo",
      "price_jpy": 5000,
      "url": "https://jp.mercari.com/item/m12345"
    }
  ]
}
```

### 3.2 既存 Playwright コードの移行
Heroku 時代に作成された `search_mercari` 等のサーバー側 Playwright コードは、以下のように Browserless 接続前提に書き換えられ、Monitoring や Fallback のタスクとしてのみ使用されます。

```python
async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp(
        f"wss://chrome.browserless.io?token={BROWSERLESS_API_KEY}"
    )
    # 以降は既存のスクレイピングロジック
```
