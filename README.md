# MarginScout v2.0 - eBay 爆益商品リサーチプラットフォーム

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## 概要

**MarginScout** は、日本の仕入れ元（Mercari、Yahoo Flea、Hardoff など）から商品を探索し、
eBay での参考相場を調査、自動的に利益を計算するリサーチ専用プラットフォームです。

### 特徴

- 🔍 **4つの仕入れ元を同時検索** - Mercari, Yahoo Flea Market, Yahoo Auction, Hardoff
- 💰 **正確な利益計算** - eBay 手数料（13.6% + $0.40）+ 国際送料を自動計算
- 📦 **複数キャリア対応** - 日本郵政 EMS と FedEx International Economy
- 🤖 **自動商品マッチング** - Jaccard 類似度による精密マッチング
- 📊 **完全なトレーサビリティ** - 監査ログ（JSONL）で全処理を記録
- ⚡ **高速処理** - 平均 1.8 秒/件の高速リサーチ

## インストール

### 前提条件

- Python 3.11+
- eBay Developer アカウント（Browse API アクセス権）
- Playwright（Chrome / Chromium）

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/nario0715masa0619-create/margin-scout.git
cd margin-scout

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
.\venv\Scripts\Activate.ps1  # Windows

# 依存パッケージをインストール
pip install -r requirements.txt
playwright install chromium

# 環境変数を設定
cp .env.example .env
# .env を編集して eBay API 認証情報を入力
```

## 使用方法

### 1. リサーチの実行

実運用スクリプトを使用して、指定したカテゴリとキーワードで一括リサーチを行います。

```bash
python test_operational_multicat_nonmock.py
```

### 2. 結果の確認

処理が完了すると、以下の結果が `output_operational_test` フォルダに出力されます。

- `research_results.csv`: 抽出された商品リストと正確な利益計算結果（黒字・赤字判定含む）
- `test_report.json`: 詳細な実行メトリクスと成功率サマリ
- `test_run.log`: 実行時の詳細なログ情報

## アーキテクチャ

MarginScout v2.0 は以下の主要モジュールで構成されています。

- **Source Adapters** (`src/source_adapters/`): 日本の各プラットフォームから並列スクレイピングで商品データを抽出
- **eBay Integration** (`src/ebay_integration/`): eBay Browse API を使用した市場相場のリサーチ
- **Product Matcher** (`src/research_workflow/product_matcher.py`): Jaccard 類似度アルゴリズムを用いた高精度な同一商品判定
- **Profit & Shipping Calculator** (`src/research_workflow/`): 実際の国際送料（EMS / FedEx）と eBay の詳細な手数料を加味したリアルな利益計算エンジン

## ライセンス

This project is licensed under the MIT License.
