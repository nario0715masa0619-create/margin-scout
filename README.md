# MarginScout

**自動爆益商品リサーチエンジン** – 日本の商品情報から eBay で高利益な商品候補を発掘

![Status](https://img.shields.io/badge/status-Research%20App-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)

---

## 📌 MarginScout とは？

MarginScout は、**リサーチ専用ツール**です。

- ✅ **爆益候補の発掘**: 日本の仕入れ元（フリマ、リユース店舗、ショップなど）から商品を探索
- ✅ **事実ベースの分析**: 仕入れ価格と eBay 参考価格から利益を計算
- ✅ **候補の出力**: CSV 形式で比較しやすく提示

- ❌ **出品は実行しません**
- ❌ **在庫管理は対象外です**
- ❌ **注文処理は行いません**

**MarginScout は「リサーチ」に特化しています。** 出品・在庫・運用は別途ツールで行ってください。

---

## 🎯 使い方

### インストール

```bash
git clone https://github.com/nario0715masa0619-create/margin-scout.git
cd margin-scout
pip install -r requirements.txt
```

### 実行

```bash
# 基本形
python cli.py --category electronics --days 90 --min-sales 2

# オプション
python cli.py --category footwear --days 180 --min-sales 5 --output-dir result
```

### 出力

以下のファイルが生成されます：

```text
output/
├── research_results.csv ................. 爆益候補リスト（詳細）
├── research_summary.json ............... 実行結果サマリー
└── logs/
    └── research_audit_YYYYMMDD_HHMMSS.jsonl .... 監査ログ
```

## 📊 出力の見方

### research_results.csv

| 列 | 意味 |
|---|---|
| candidate_id | 候補 ID |
| product_name | 商品名 |
| source_channel | 仕入れ元（Mercari, Hardoff など） |
| source_url | 仕入れ元 URL |
| source_price | 仕入れ価格（日本円） |
| reference_sale_price | eBay 参考価格（米ドル） |
| estimated_profit | 推定利益（米ドル） |
| profit_margin_percent | 推定利益率（%） |

例:

```csv
RESEARCH-20260615-001,Sony Headphones,mercari,https://...,5000,60.00,35.00,37.5
```
→ 「日本で5000円で仕入れた商品が、eBay では60ドルで売れそう。利益35ドル、利益率37%」

## 🏗️ アーキテクチャ

```text
【ユーザー】
    ↓
カテゴリ・期間を指定
    ↓
【MarginScout】
    ├─ 仕入れ元を探索
    ├─ eBay で参考相場を検索
    └─ 利益計算
    ↓
【出力】
research_results.csv
    ↓
【ユーザーが判断】
「この商品、仕入れようかな」
```

## ✅ MarginScout の責務
- 爆益候補の発掘
- 仕入れ価格の取得
- eBay 参考価格の取得
- 利益計算
- CSV 出力

## ❌ MarginScout ではできないこと
- eBay への出品実行
- 在庫同期
- 注文管理
- 販売運用

これらは別途ツール（eBay Listing App など）で行ってください。

## 📚 ドキュメント
- MARGINSCOUT_REDEFINED.md – 思想・責務の最終定義
- API_SCOPE_DEFINITION.md – eBay API の使用範囲
- RESEARCH_DATA_MODEL_V2.md – データモデル
- PHASE2_RESEARCH_WORKFLOW.md – 処理フロー

## 🔧 技術スタック

| 項目 | 詳細 |
|---|---|
| 言語 | Python 3.11+ |
| API | eBay Browse API |
| 入力 | CLI パラメータ |
| 出力 | CSV + JSON + JSONL ログ |
| 認証 | OAuth 2.0 (Application Token) |

## 📝 ライセンス
MIT License

## 🚀 次のステップ
- [ ] eBay Browse API 認証設定
- [ ] 仕入れ元スクレイピング実装
- [ ] 商品マッチング精度向上
- [ ] 大規模データセットでのテスト

MarginScout v2.0 – リサーチ専用、シンプル、強力。
