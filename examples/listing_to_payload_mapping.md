# Listing → Payload マッピング対応表

目的: ListingReadyRecord と eBay Payload Input の対応を明確化

## 項目別マッピング

| Listing項目 | Payload項目 | 変換処理 | 説明 |
|---|---|---|---|
| candidate_id | audit_trail.candidate_id | そのまま | 監査用に保持 |
| sku | payload.sku | そのまま | 出品用SKU |
| product_name | payload.title の入力 | Template適用 | title生成の基盤 |
| category | payload.category + audit | Category mapper | 内部→eBay変換 |
| condition | payload.condition | Condition mapper | 正規化変換 |
| brand | item_specifics.Brand | Optional | title補助、item_specificsに |
| model_number | item_specifics.Model | Optional | title補助、item_specificsに |
| reference_price | audit_trail.observed_price | 監査用 | 参考値（出品価格ではない） |
| image_dir | payload.images | Directory→List | ローカルパス列挙 |
| image_count | payload.images 長 | Count | 画像数確認 |
| user_notes | payload.description の入力 | Sanitize + escape | 公開description構成 |
| user_tags | audit_trail.user_tags | 監査用 | 内部用タグ保持 |
| source_url | audit_trail.source_url | 監査用 | 参考価格出典 |
| source_type | audit_trail.source_type | 監査用 | データ取得元 |
| observed_date | audit_trail.observed_date | 監査用 | 観測タイムスタンプ |
| listing_status | (検証に使用) | - | readiness判定に使用 |
| validation_status | validation_report | - | payload readiness決定 |
| completeness_status | validation_report | - | incomplete判定に使用 |

## 変換ルール詳細

### title 変換

```
入力: product_name = "Canon EF 50mm f/1.8 STM"
      brand = "Canon"
      condition = "new"

ルール: Template A = "{BRAND} {PRODUCT_NAME} - {CONDITION}"

出力: title = "Canon EF 50mm f/1.8 STM - new"
      (80文字以下に制限)
```

### description 変換

```
入力: product_name, brand, condition, user_notes

ルール: 
  1. Header = "{PRODUCT_NAME}\n{BRAND} | {CONDITION}"
  2. Body = sanitize_html(user_notes)
  3. Footer = "【注意】本出品は MarginScout により..."

出力: description = header + body + footer
      (HTML escape済み)
```

### category 変換

```
入力: category = "Camera Lenses"

ルール: CATEGORY_MAP["Camera Lenses"] = {
          "ebay_category_id": "625",
          "confidence": "high"
        }

出力: payload.category = "Camera Lenses"
      (ebay_category_id は Phase 5 で決定)
```

### condition 変換

```
入力: condition = "new"

ルール: CONDITION_MAP["new"] = "new"

出力: payload.condition = "new"
```

### images 変換

```
入力: image_dir = "data/images/MARGIN-20260613-0001/"
      image_count = 3

ルール: 
  1. ディレクトリ走査
  2. ゼロパディング順序 (01.jpg, 02.jpg, ...)
  3. 完全パスで返す

出力: images = [
        "data/images/MARGIN-20260613-0001/01.jpg",
        "data/images/MARGIN-20260613-0001/02.jpg",
        "data/images/MARGIN-20260613-0001/03.jpg"
      ]
```

## Payload で追加・変更される項目

| 項目 | Listing | Payload | 説明 |
|---|---|---|---|
| price | None | None | Phase 5で決定 |
| quantity | 1 | 1 | default値で固定 |
| item_specifics | - | {Brand, Model} | 新規追加（Listing には非含） |
