# MarginScout

**自動爆益商品リサーチエンジン** – eBay で高利益商品を自動発掘

![Status](https://img.shields.io/badge/Status-Research%20Phase%201--2-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)

---

## 📌 役割分担

**MarginScout** は商品リサーチ専門の Research App です。eBay 出品・在庫・注文管理は別リポジトリ「eBay Listing App」で実装されています。

| 項目 | MarginScout | eBay Listing App |
|---|---|---|
| 商品リサーチ | ✅ | ❌ |
| 価格分析 | ✅ | ❌ |
| CSV 出力 | ✅ | ❌ |
| eBay 出品 | ❌ | ✅ |
| 在庫同期 | ❌ | ✅ |
| 注文管理 | ❌ | ✅ |

📦 **eBay Listing App**: https://github.com/nario0715masa0619-create/ebay-listing-app

---

## 概要

**MarginScout** は、小売店の商品リストを自動分析し、eBay での高利益販売候補を発掘するリサーチエンジンです。

- 🔍 **自動商品リサーチ**: 商品候補の自動収集・分析
- 📊 **価格分析**: eBay 相場データ自動取得・分析
- 💰 **利益評価**: 利益率・ROI 自動計算
- 📁 **CSV 出力**: リサーチ結果を CSV 形式で出力
- 📋 **Listing Seed CSV**: eBay Listing App への連携

---

## クイックスタート

### 1. インストール
\\\ash
git clone https://github.com/nario0715masa0619-create/margin-scout.git
cd margin-scout
pip install -r requirements.txt
\\\

### 2. 設定
\\\ash
cp .env.example .env
# .env を編集して必要な設定を行う
\\\

### 3. 実行
\\\ash
python -m src.research_workflow.research_processor input.csv
\\\

### 4. 出力
- research_results.csv – リサーチ結果
- listing_seed.csv – eBay Listing App への入力
- research_audit_YYYYMMDD_HHMMSS.log – 監査ログ

## 主な機能
| 機能 | 説明 |
|---|---|
| Product Normalization | 商品情報の正規化・クレンジング |
| Category Mapping | eBay カテゴリへの自動マッピング |
| Price Analysis | eBay 市場相場の自動取得・分析 |
| Profit Evaluation | 利益率・リスク評価 |
| CSV I/O | 入出力 CSV 管理 |

## アーキテクチャ
\\\	ext
Input CSV (小売店商品)
         ↓
  [Research Workflow]
  1. Normalizer
  2. Category Mapper
  3. Price Analyzer
  4. Profit Evaluator
         ↓
Output CSV (research_results.csv)
     + Listing Seed CSV
     + Audit Log
         ↓
[eBay Listing App] ← 別リポジトリで実装
\\\

## ドキュメント
- MARGINSCOUT_SCOPE.md – スコープ定義
- RESEARCH_DATA_MODEL.md – データモデル
- PHASE2_RESEARCH_WORKFLOW.md – Phase 2 実装仕様
- SEPARATION_REPORT.md – 分離完了報告書

## スコープ
### ✅ MarginScout が責務を取る
- 商品リサーチ・分析
- CSV 出力
- 監査ログ

### ❌ MarginScout は責務を取らない
- eBay 出品・OAuth・Live API
- 在庫管理・注文処理
- → これらは eBay Listing App で実装

## テスト
\\\ash
# Unit テスト
pytest tests/ -v

# カバレッジ
pytest tests/ --cov=src
\\\

## 構成ファイル
- .env – 設定（API キー等）
- requirements.txt – Python 依存ライブラリ
- setup.py – パッケージ設定

## ライセンス
MIT License

## 関連リポジトリ
- eBay Listing App – 出品・在庫・注文管理
- MarginScout v1.0 – Research Phase 1-2 (Production-Ready)
