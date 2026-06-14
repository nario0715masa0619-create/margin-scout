# eBay API スコープ定義

**作成日**: 2026-06-15
**対象**: MarginScout での eBay API 利用範囲

---

## 使用する eBay API

### Browse API (使用対象 ✅)

| API | 用途 | 理由 |
|---|---|---|
| `GET /buy/browse/v1/item_summary/search` | 商品検索 | 参考価格・商品情報取得 |
| `GET /buy/browse/v1/item/{itemId}` | 商品詳細取得 | 詳細情報・画像取得 |

**認証方法**: Application Token (OAuth Client Credentials)

---

## 使用しない eBay API

### Sell API (使用対象外 ❌)

| カテゴリ | 理由 |
|---|---|
| Inventory API | 在庫管理は MarginScout 責務外 |
| Offer API | 出品作成は MarginScout 責務外 |
| Listing API | 出品管理は MarginScout 責務外 |
| Fulfillment API | 注文管理は MarginScout 責務外 |
| Order API | 注文取得は MarginScout 責務外 |
| Account API | セラーアカウント管理は MarginScout 責務外 |

### その他の API

- Taxonomy API: 不要（事前定義カテゴリで十分）
- Marketing API: 不要
- Logistics API: 不要

---

## 認証設計

### Browse API 認証

**方式**: OAuth 2.0 Client Credentials Flow

**必要な認定情報**:
- Client ID (App ID)
- Client Secret
- Scope: `https://api.ebay.com/oauth/api_scope`

**実装場所**:
- `.env` ファイル：

```env
EBAY_BROWSE_CLIENT_ID=xxx
EBAY_BROWSE_CLIENT_SECRET=xxx
```

**有効期限管理**:
- Token に有効期限がある場合は自動リフレッシュ

---

## 認証しない API

- **Sell 系 API**: OAuth 認証が必要だが、MarginScout では使用しないため実装不要

---

## API 呼び出し設計

### 検索クエリ例

```http
GET /buy/browse/v1/item_summary/search?q=Sony%20headphones&limit=50
```

### レスポンス処理

- 検索結果から商品情報を抽出
- 参考価格を取得
- CSV に記録

---

## 制限事項

- API レート制限: 5000 リクエスト / 日 (標準)
- 必要なら `limit` パラメータで調整

---

**この定義に基づき、Browse API のみを実装する。**
