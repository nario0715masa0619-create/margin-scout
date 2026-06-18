# API Specification

## 1. 概要
MarginScout SaaS バックエンドが公開する REST API の仕様です。
Frontend (ダッシュボード) および Browser Extension から呼び出されます。

## 2. 認証 (Authentication)
すべてのセキュアなエンドポイントは JWT (JSON Web Token) による認証を要求します。
- **Header**: `Authorization: Bearer <token>`
- **Note**: クライアントから送信されるリクエストボディに `user_id` は含めません。バックエンドは JWT トークンの検証時にペイロードから `user_id` を自動的に抽出し、操作を解決・認可します。

---

## 3. 主要エンドポイント

### 3.1 Captures API (Extension 連携用)

フリマサイト（Mercari 等）から Browser Extension が抽出した DOM データを SaaS に送信・保存・解析するためのエンドポイントです。

#### `POST /api/v1/captures`
- **概要**: ブラウザ上で抽出された商品一覧をバックエンドにインポートし、裏側で eBay 相場とのマッチング（利益計算）を非同期または同期的に実行します。
- **Request Body**:
  ```json
  {
    "source_domain": "mercari.com",
    "search_keyword": "Pokemon Card Pikachu",
    "items": [
      {
        "title": "Pikachu Promo",
        "price_jpy": 5000,
        "url": "https://jp.mercari.com/item/m12345",
        "image_url": "https://..."
      }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "import_session_id": "uuid-v4",
    "status": "processing",
    "items_received": 1
  }
  ```

#### `GET /api/v1/captures/{import_session_id}`
- **概要**: 上記でインポートしたセッションの処理状況と結果（利益計算済みのデータ）を取得します。
- **Response**:
  ```json
  {
    "status": "completed",
    "results": [
      {
        "source_item_id": "uuid",
        "title": "Pikachu Promo",
        "source_price_jpy": 5000,
        "ebay_matches": [
          {
            "ebay_title": "Pokemon Pikachu Promo NM",
            "ebay_price_usd": 100.0,
            "estimated_profit_jpy": 8000
          }
        ]
      }
    ]
  }
  ```

### 3.2 Authentication API

#### `POST /api/v1/auth/login`
- **Request**: `email`, `password`
- **Response**: `access_token`, `token_type`

### 3.3 Dashboard / User APIs

#### `GET /api/v1/users/me/quota`
- **概要**: ユーザーの現在の利用状況（今月のリサーチ回数、保存済アイテム数など）と契約プランの制限を返します。
- **Response**:
  ```json
  {
  ```json
  {
    "plan": "basic",
    "monthly_captures_used": 150,
    "monthly_captures_limit": 500
  }
  ```

---

## 4. P2-2a.5 確定 API 仕様

### エンドポイント一覧

1. **GET `/api/v1/captures`**
   - **説明**: ImportSession 一覧（ページング対応）
   - **認証**: Bearer token（user_id 自動フィルタ）
   - **クエリ**: `?limit=20&offset=0`
   - **レスポンス**: `sessions[]`, `total`, `limit`, `offset`

2. **GET `/api/v1/captures/{capture_id}`**
   - **説明**: ImportSession 詳細
   - **認証**: Bearer token
   - **所有権**: user_id で確認（他ユーザー → 404）
   - **レスポンス**: `id`, `source`, `import_type`, `item_count`, `processed_count`, `matched_count`, `error_count`, `created_at`, `completed_at`, `items[]`

3. **GET `/api/v1/captures/{capture_id}/items`**
   - **説明**: セッション内の SourceItem 一覧
   - **認証**: Bearer token
   - **クエリ**: `?limit=100&offset=0`
   - **所有権**: capture_id の user_id 確認
   - **レスポンス**: `items[]`, `total`, `limit`, `offset`

4. **POST `/api/v1/captures/{capture_id}/export/csv`**
   - **説明**: セッションの CSV エクスポート
   - **認証**: Bearer token
   - **入力**: なし（capture_id で確定）
   - **所有権**: capture_id の user_id 確認
   - **レスポンス**: Content-Type: `text/csv`, Content-Disposition: `attachment`
   - **CSV ヘッダ**: 商品名,ソース,フリマ価格,eBay価格,利益,利益率,%

5. **GET `/api/v1/saved-items`**
   - **説明**: 保存済み SourceItem 一覧（全セッション）
   - **認証**: Bearer token（user_id 自動フィルタ）
   - **クエリ**: `?limit=100&offset=0&source=mercari&sort=profit_desc`
   - **レスポンス**: `items[]`, `total`, `limit`, `offset`

6. **GET `/api/v1/saved-items/{item_id}`**
   - **説明**: SourceItem 詳細（ProfitSnapshot, EbayMatch 含む）
   - **認証**: Bearer token
   - **所有権**: item_id の user_id 確認（source_item → import_session → user_id）
   - **レスポンス**: `id`, `title`, `source`, `source_price_jpy`, `url`, `image_url`, `seller_name`, `condition`, `category`, `ebay_price_jpy`, `ebay_title`, `profit_jpy`, `profit_margin_pct`, `exchange_rate_usd_jpy`, `match_score`, `match_status`, `import_session_id`, `created_at`

7. **POST `/api/v1/saved-items/export/csv`**
   - **説明**: 複数 SourceItem の CSV エクスポート
   - **認証**: Bearer token
   - **入力**: `{ "item_ids": ["uuid1", "uuid2", ...] }`
   - **所有権**: 全 item_ids が current_user_id 配下であること確認
   - **レスポンス**: CSV ファイル

### 共通仕様

**ページング:**
- すべてのリスト取得エンドポイントに `?limit=N&offset=M` をサポート
- デフォルト: `limit=20`, `offset=0`
- 最大値: `limit ≤ 100`（超過時は 400 エラー）
- レスポンスに常に `total`（総件数）を含める

**日時フォーマット:**
- すべて ISO 8601 UTC（例: `2026-06-17T10:30:00Z`）

**Rate Limit ヘッダー (すべてのレスポンスに含める):**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 456
X-RateLimit-Reset: 1718623200
```

**認証エラー:**
- `401`: 認証なし / トークン無効
- `403`: 権限なし（他ユーザーデータアクセス）
- `404`: リソースなし

**バリデーションエラー:**
- `400`: ペイロード検証失敗 / 不正な クエリパラメータ
- `422`: ペイロード型エラー

**エラーレスポンス形式:**
```json
{
  "detail": "Error message"
}
```

### レスポンス形式詳細

**GET `/api/v1/captures` (ImportSession 一覧):**
```json
{
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "source": "mercari",
      "import_type": "manual",
      "item_count": 10,
      "processed_count": 10,
      "matched_count": 8,
      "error_count": 0,
      "created_at": "2026-06-17T10:30:00Z",
      "completed_at": "2026-06-17T10:31:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**GET `/api/v1/captures/{capture_id}` (ImportSession 詳細):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "source": "mercari",
  "import_type": "manual",
  "item_count": 10,
  "processed_count": 10,
  "matched_count": 8,
  "error_count": 0,
  "created_at": "2026-06-17T10:30:00Z",
  "completed_at": "2026-06-17T10:31:00Z",
  "items": [
    {
      "id": "uuid",
      "title": "iPhone 14 Pro",
      "source_price_jpy": 95000,
      "ebay_price_jpy": 152000,
      "profit_jpy": 57000,
      "profit_margin_pct": 60.0,
      "status": "matched"
    }
  ]
}
```

**GET `/api/v1/captures/{capture_id}/items` (セッション内 SourceItem):**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "iPhone 14 Pro",
      "source": "mercari",
      "source_price_jpy": 95000,
      "url": "https://mercari.jp/item/m123",
      "image_url": "https://...",
      "seller_name": "User123",
      "condition": "new",
      "ebay_price_jpy": 152000,
      "profit_jpy": 57000,
      "profit_margin_pct": 60.0,
      "match_score": 0.95,
      "match_status": "matched",
      "created_at": "2026-06-17T10:30:00Z"
    }
  ],
  "total": 10,
  "limit": 100,
  "offset": 0
}
```

**GET `/api/v1/saved-items` (保存済み SourceItem 一覧):**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "iPhone 14 Pro",
      "source": "mercari",
      "source_price_jpy": 95000,
      "url": "https://mercari.jp/item/m123",
      "ebay_price_jpy": 152000,
      "profit_jpy": 57000,
      "profit_margin_pct": 60.0,
      "import_session_id": "uuid",
      "created_at": "2026-06-17T10:30:00Z"
    }
  ],
  "total": 123,
  "limit": 100,
  "offset": 0
}
```

**GET `/api/v1/saved-items/{item_id}` (SourceItem 詳細):**
```json
{
  "id": "uuid",
  "title": "iPhone 14 Pro",
  "source": "mercari",
  "source_price_jpy": 95000,
  "url": "https://mercari.jp/item/m123",
  "image_url": "https://...",
  "seller_name": "User123",
  "condition": "new",
  "category": "smartphones",
  "ebay_price_jpy": 152000,
  "ebay_title": "Apple iPhone 14 Pro Max",
  "profit_jpy": 57000,
  "profit_margin_pct": 60.0,
  "exchange_rate_usd_jpy": 160.36,
  "match_score": 0.95,
  "match_status": "matched",
  "import_session_id": "uuid",
  "created_at": "2026-06-17T10:30:00Z"
}
```
