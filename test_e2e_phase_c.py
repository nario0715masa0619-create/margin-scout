"""Phase C: 最小E2E確認テスト"""
import sys
import os
import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# パスを追加
sys.path.insert(0, os.path.dirname(__file__))

# MarginScout モジュールをインポート
from src.ebay_integration import EbayAuthHandler, EbayBrowseApiClient
from src.research_workflow.ebay_searcher import EbaySearcher
from src.research_workflow.csv_handler import CSVHandler
from src.research_workflow.audit_logger import AuditLogger

def run_e2e_test():
    """最小E2Eテストを実行"""
    
    print("=" * 70)
    print("MarginScout Phase C: 最小E2E確認テスト")
    print("=" * 70)
    
    # 入力ファイルパス
    input_file = "examples/e2e_input_sample.csv"
    output_dir = "output_e2e"
    
    # 出力ディレクトリ作成
    Path(output_dir).mkdir(exist_ok=True)
    
    # 監査ログ初期化
    audit_logger = AuditLogger(output_dir)
    
    print(f"\n[Input] Reading from: {input_file}")
    
    # 入力CSVを読み込み
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            input_products = list(reader)
    except FileNotFoundError:
        print(f"ERROR: Input file not found: {input_file}")
        return False
    
    print(f"[Input] Loaded {len(input_products)} products")
    
    # ============================================
    # eBay API 初期化（実装フェーズではスキップ）
    # ============================================
    # 本来ここで eBay API を初期化しますが、
    # まだ実 API credentials がないため、
    # ここではモック結果を使用します
    
    print("\n[Processing] Starting search and match...")
    
    results = []
    
    for idx, product in enumerate(input_products, 1):
        print(f"\n  [{idx}/{len(input_products)}] Processing: {product.get('product_name')}")
        
        # NOTE: 実装フェーズでは実際の eBay API を呼び出します
        # 現在はダミーマッチング結果を生成
        
        result = {
            "candidate_id": f"E2E-{datetime.now().strftime('%Y%m%d')}-{idx:04d}",
            "product_name": product.get('product_name'),
            "source_channel": "sample_input",
            "source_url": product.get('source_url', ''),
            "source_price": Decimal(product.get('source_price', 0)),
            "source_currency": "JPY",
            "condition_text": product.get('condition', ''),
            "observed_at": datetime.now().isoformat(),
            "reference_market": "ebay",
            "reference_item_id": f"mock-{idx}",
            "reference_item_url": f"https://ebay.com/itm/mock-{idx}",
            "reference_sale_price": Decimal(str(float(product.get('source_price', 0)) / 150 * 1.5)),  # 簡易計算
            "reference_currency": "USD",
            "estimated_profit": Decimal("50"),  # ダミー値
            "profit_margin_percent": 25.0,
            "notes": "Phase C test - mock data",
        }
        
        results.append(result)
        audit_logger.log_event("process_success", {"sku": product.get('product_name')})
        
        print(f"    ✓ Matched (mock)")
    
    # ============================================
    # 出力
    # ============================================
    
    print(f"\n[Output] Writing results...")
    
    # research_results.csv を出力
    output_csv = f"{output_dir}/research_results.csv"
    if results:
        fieldnames = list(results[0].keys())
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"  ✓ Wrote: {output_csv}")
    
    # サマリーを出力
    summary = {
        "execution_timestamp": datetime.now().isoformat(),
        "total_input": len(input_products),
        "successful": len(results),
        "skipped": 0,
        "output_files": {
            "research_results_csv": output_csv,
            "audit_log": str(audit_logger.log_path),
        }
    }
    
    print(f"\n[Summary]")
    print(f"  Total input: {summary['total_input']}")
    print(f"  Successful: {summary['successful']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Output directory: {output_dir}")
    
    print("\n" + "=" * 70)
    print("✅ Phase C E2E Test Complete")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    success = run_e2e_test()
    sys.exit(0 if success else 1)
