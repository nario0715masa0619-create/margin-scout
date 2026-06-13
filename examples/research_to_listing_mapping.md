# Research to Listing CSV マッピング対応表

目的: Research CSV の各列が Listing CSV でどう扱われるかを明確化

## 列別マッピング

| # | Research列 | Listing での扱い | 変換ルール | 説明 |
|---|---|---|---|---|
| 1 | candidate_id | そのまま保持 | No change | 追跡性確保のため必ず保持 |
| 2 | product_name | そのまま使用 | Trim & validate | eBay title の基盤 |
| 3 | reference_price | そのまま保持 | Decimal check | 参考価格として記録（実出品価格は別） |
| 4 | currency | そのまま保持 | Enum check | 将来の通貨変換で使用 |
| 5 | brand | 補完判定後、使用 | Optional + Pending Review | eBay title に使用可能 |
| 6 | model_number | 補完判定後、使用 | Optional + Pending Review | eBay title / description に使用可能 |
| 7 | category | マッピング対象 | eBay category ID へ変換 | 必須、未設定は Hard Error |
| 8 | product_url | 監査フィールドとして保持 | No change | source_url として記録 |
| 9 | source_type | 監査フィールドとして保持 | Enum check | どこから取得したか追跡 |
| 10 | observed_date | 監査フィールドとして保持 | DateTime check | 観測タイムスタンプ |
| 11 | condition | 正規化・マッピング | eBay condition へ | new / used / refurbished に統一 |
| 12 | user_notes | 参考フィールドとして保持 | No change | listing note の参考 |
| 13 | user_tags | 参考フィールドとして保持 | List parse | 内部用タグとして保持 |
| 14 | judgement_flag | 参考フィールドとして保持 | No change | 出品判定補助 |
| 15 | research_status | フィルタ条件 | confirmed のみ取込 | 除外・未確定は skip |

## Listing CSV で追加される列

| 列名 | 説明 | 由来 |
|---|---|---|
| sku | 出品用SKU (MARGIN-YYYYMMDD-NNNN) | 自動採番 |
| image_dir | 画像ディレクトリパス | SKU から自動解決 |
| image_count | 画像数 | ディレクトリ走査 |
| source_url | product_url の別名 | 監査用 |
| listing_status | ready / pending_review / incomplete | 補完状態判定 |
| transformation_timestamp | 変換実施日時 | 現在時刻 |
