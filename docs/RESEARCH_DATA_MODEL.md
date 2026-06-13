# MarginScout: リサーチデータモデル仕様書

**作成日**: 2026-06-13  
**バージョン**: 0.1  
**ステータス**: ドラフト / 設計段階

---

## リサーチ候補エンティティ（ResearchCandidate）

### フィールド一覧

- candidate_id: str — 一意識別子
- product_name: str — 商品名
- product_url: str — 参考価格観測元 URL
- source_type: str — ソース種別
- reference_price: Decimal — 参考価格
- currency: str — 通貨コード
- observed_date: datetime — 価格観測日時
- data_source: str — 取得手段
- brand: str (optional) — ブランド名
- model_number: str (optional) — 型番
- category: str (optional) — カテゴリ
- price_low: Decimal (optional) — 価格帯（最低）
- price_high: Decimal (optional) — 価格帯（最高）
- condition: str (optional) — 商品状態
- collection_timestamp: datetime — 収集日時
- user_notes: str (optional) — ユーザーメモ
- user_tags: List[str] — ユーザータグ
- judgement_flag: str (optional) — 判定フラグ
- research_status: str — ステータス
- csv_export_ready: bool — CSV 出力対象フラグ
- created_at: datetime — 作成日時
- updated_at: datetime — 最終更新日時

---

## CSV 出力スキーマ

### CSV ヘッダー定義

```
candidate_id, product_name, reference_price, currency, brand,
model_number, category, product_url, source_type, observed_date,
condition, user_notes, user_tags, judgement_flag, research_status
```

### CSV 出力例

```csv
candidate_id,product_name,reference_price,currency,brand,model_number,category,product_url,source_type,observed_date,condition,user_notes,user_tags,judgement_flag,research_status
ms-res-20260613-0001,Canon EF 50mm f/1.8 STM,189.99,USD,Canon,EF50STM,Camera Lenses,https://www.ebay.com/itm/324901234567,ebay_listing,2026-06-13T14:30:00Z,new,状態良好・レンズクリア,high-demand;checked,promising,confirmed
ms-res-20260613-0002,Nike Air Force 1 US9,110.00,USD,Nike,AF1-US9,Footwear,https://www.ebay.com/itm/324901234568,ebay_listing,2026-06-13T14:35:00Z,new,サイズ確認済み,checked,promising,confirmed
```

---

**改版履歴**:
- v0.1 (2026-06-13) — 初版作成
