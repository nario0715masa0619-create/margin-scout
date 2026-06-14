# Research Data Model v2.0

**作成日**: 2026-06-15
**変更**: MarginScout 再定義に合わせた最小化

---

## ResearchCandidate データ構造

```python
@dataclass
class ResearchCandidate:
    # 候補識別
    candidate_id: str                    # RESEARCH-YYYYMMDD-xxxxx
    product_name: str                    # 正規化済み商品名
    
    # 仕入れ元情報（事実）
    source_channel: str                  # mercari, hardoff, yahoo_fleamarket など
    source_url: str                      # 仕入れ元 URL
    source_price: Decimal                # 仕入れ価格
    source_currency: str                 # JPY など
    condition_text: Optional[str]        # 商品状態記述
    observed_at: datetime                # 観測日時
    
    # eBay 参考市場情報
    reference_market: str                # "ebay"
    reference_item_id: Optional[str]     # eBay item ID
    reference_item_url: Optional[str]    # eBay 商品 URL
    reference_sale_price: Decimal        # eBay 参考販売価格
    reference_currency: str              # USD など
    
    # 利益計算（参考値）
    estimated_profit: Decimal            # 推定利益（USD）
    profit_margin_percent: float         # 推定利益率（%）
    
    # メタデータ
    brand: Optional[str] = None
    model_number: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

## 削除した項目

以下の項目は Research App では不要 なため削除:

- judgement_flag → 判定はユーザーが行う
- research_status ("DRAFT", "CONFIRMED" など) → 出品対象決定はユーザーが行う
- csv_export_ready → 全候補を出力
- user_notes, user_tags → 入力段階では不要
- 仕入れ先信頼度スコア → 評価しない

## 出力 CSV 構造

### research_results.csv

```csv
candidate_id,product_name,source_channel,source_url,source_price,source_currency,observed_at,reference_market,reference_item_url,reference_sale_price,reference_currency,estimated_profit,profit_margin_percent,notes
RESEARCH-20260615-0001,Sony Headphones,mercari,https://mercari.com/item/xxx,5000,JPY,2026-06-15T10:00:00,ebay,https://ebay.com/itm/xxx,60.00,USD,35.00,37.5,Good condition
```

この定義で、最小限にして最大限に機能する Research App を実現する。
