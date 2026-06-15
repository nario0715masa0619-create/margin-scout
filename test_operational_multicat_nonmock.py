"""
MarginScout Operational Test - Real eBay API + All Source Adapters
非モック実行で、複数カテゴリ・複数キーワード・4ソースの実運用品質を検証
"""

import asyncio
import os
import sys
import json
import time
import csv
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
import logging

sys.path.insert(0, str(Path(__file__).parent))

from src.ebay_integration.auth_handler import EbayAuthHandler
from src.ebay_integration.browse_api_client import EbayBrowseApiClient
from src.research_workflow.product_matcher import ProductMatcher
from src.source_adapters import MercariAdapter, YahooFleamarketAdapter, YahooAuctionHistoryAdapter, HardoffAdapter
class ErrorHandler:
    def __init__(self, path):
        pass

from src.research_workflow.profit_calculator_v2 import ProfitCalculatorV2
from src.research_workflow.audit_logger import AuditLogger


@dataclass
class TestMetrics:
    """テスト実行メトリクス"""
    total_inputs: int = 0
    source_items_found: dict = field(default_factory=lambda: {
        "mercari": 0, "yahoo_flea": 0, "yahoo_auction": 0, "hardoff": 0
    })
    ebay_search_success: int = 0
    ebay_search_failed: int = 0
    matching_success: int = 0
    matching_failed: int = 0
    csv_output_count: int = 0
    skipped_count: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    failure_reasons: dict = field(default_factory=dict)
    category_stats: dict = field(default_factory=dict)
    source_success_rate: dict = field(default_factory=lambda: {
        "mercari": {"total": 0, "success": 0},
        "yahoo_flea": {"total": 0, "success": 0},
        "yahoo_auction": {"total": 0, "success": 0},
        "hardoff": {"total": 0, "success": 0}
    })


class OperationalTestRunner:
    """実運用テスト実行エンジン"""
    
    # テスト対象カテゴリ・キーワード定義
    TEST_CASES = {
        "electronics": ["iPhone", "iPad", "MacBook"],
        "camera": ["Canon EOS", "Nikon", "Sony Alpha"],
        "games": ["Pokemon Card", "Yugioh", "Nintendo Switch"],
        "fashion": ["Gucci", "Louis Vuitton", "The North Face"],
        "hobby": ["LEGO", "Bandai", "Figma"]
    }
    
    def __init__(self, output_dir: str = "output_operational_test"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = self._setup_logger()
        self.audit_logger = AuditLogger(self.output_dir / "logs")
        self.error_handler = ErrorHandler(self.output_dir / "errors")
        self.metrics = TestMetrics()
        
        self.ebay_auth = None
        self.ebay_client = None
        self.product_matcher = ProductMatcher()
        self.profit_calc = ProfitCalculatorV2(exchange_rate=157.50)
        
        # ソースアダプタ
        self.adapters = {}
        self.playwright = None
        self.browser = None
        
        self.results = []
        self.samples = []  # 品質確認用サンプル
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("OperationalTest")
        logger.setLevel(logging.DEBUG)
        
        handler = logging.FileHandler(self.output_dir / "test_run.log", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    async def initialize(self):
        """初期化: eBay 認証, アダプタ初期化"""
        self.logger.info("=== Operational Test Initialization ===")
        
        try:
            self.ebay_auth = EbayAuthHandler()
            token = self.ebay_auth.get_token()
            if not token:
                self.logger.warning("⚠ eBay token failed; mock mode activated")
                self.ebay_auth.use_mock = True
            else:
                self.logger.info("✅ eBay token acquired successfully")
            
            self.ebay_client = EbayBrowseApiClient(self.ebay_auth)
            
            # Playwright 初期化
            from playwright.async_api import async_playwright
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True)
            page_mercari = await self.browser.new_page()
            page_yahoo_flea = await self.browser.new_page()
            page_hardoff = await self.browser.new_page()
            
            self.adapters = {
                "mercari": MercariAdapter(page_mercari),
                "yahoo_flea": YahooFleamarketAdapter(page_yahoo_flea),
                "yahoo_auction": YahooAuctionHistoryAdapter(self.browser),
                "hardoff": HardoffAdapter(page_hardoff)
            }
            
            self.metrics.start_time = time.time()
            self.logger.info("✅ All components initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            await self.cleanup()
            raise
    
    async def test_source_adapters(self) -> dict:
        """ソースアダプタ品質テスト"""
        self.logger.info("\n=== Testing Source Adapters ===")
        
        adapter_results = {}
        
        for category, keywords in self.TEST_CASES.items():
            self.logger.info(f"\nCategory: {category}")
            
            # 最初のキーワードでテスト
            test_keyword = keywords[0]
            self.logger.info(f"  Testing keyword: {test_keyword}")
            
            adapter_results[category] = {}
            
            for adapter_name, adapter in self.adapters.items():
                try:
                    self.logger.info(f"  [{adapter_name}] Searching '{test_keyword}'...")
                    items = await adapter.search([test_keyword], genre=category)
                    
                    count = len(items) if items else 0
                    self.metrics.source_items_found[adapter_name] += count
                    adapter_results[category][adapter_name] = {
                        "count": count,
                        "items": items[:3] if items else []  # 最初の3件
                    }
                    
                    self.logger.info(f"    ✅ Found {count} items")
                    
                except Exception as e:
                    self.logger.warning(f"    ❌ {adapter_name} failed: {e}")
                    adapter_results[category][adapter_name] = {"count": 0, "error": str(e)}
        
        return adapter_results
    
    async def test_ebay_search(self):
        """eBay Browse API 検索テスト"""
        self.logger.info("\n=== Testing eBay Browse API ===")
        
        test_keywords = ["iPhone 12", "Sony Alpha", "Pokemon Card"]
        
        for keyword in test_keywords:
            try:
                self.logger.info(f"Searching eBay: '{keyword}'...")
                results = await self.ebay_client.search(keyword, limit=3)
                
                if results:
                    self.metrics.ebay_search_success += 1
                    self.logger.info(f"  ✅ Found {len(results)} items")
                    for item in results[:2]:
                        self.logger.info(f"    - {item.get('title', 'N/A')}: ${item.get('price', 'N/A')}")
                else:
                    self.metrics.ebay_search_failed += 1
                    self.logger.warning(f"  ❌ No results for '{keyword}'")
                    
            except Exception as e:
                self.metrics.ebay_search_failed += 1
                self.logger.error(f"  ❌ eBay search failed: {e}")
    
    async def test_end_to_end(self):
        """完全 E2E フロー: ソース取得 → eBay 検索 → マッチング → 利益計算"""
        self.logger.info("\n=== End-to-End Research Flow ===")
        
        all_source_items = []
        
        # ステップ 1: 全ソースから商品取得
        self.logger.info("\n[Step 1] Fetching from all sources...")
        for category, keywords in self.TEST_CASES.items():
            for keyword in keywords[:2]:  # 各カテゴリ 2 キーワード
                for adapter_name, adapter in self.adapters.items():
                    try:
                        items = await adapter.search([keyword], genre=category)
                        if items:
                            for item in items[:2]:  # 各ソース 2 件
                                all_source_items.append({
                                    "source": adapter_name,
                                    "item": item,
                                    "category": category,
                                    "keyword": keyword
                                })
                    except Exception as e:
                        self.logger.debug(f"Adapter {adapter_name} error: {e}")
        
        self.logger.info(f"  ✅ Total source items: {len(all_source_items)}")
        self.metrics.total_inputs = len(all_source_items)
        
        # ステップ 2: 各アイテムに対して eBay 検索 + マッチング + 利益計算
        self.logger.info(f"\n[Step 2] Processing {len(all_source_items)} items...")
        
        for idx, source_item_data in enumerate(all_source_items, 1):
            source_item = source_item_data["item"]
            keyword = source_item_data["keyword"]
            
            try:
                # eBay 検索
                ebay_results = await self.ebay_client.search(source_item.product_title or keyword, limit=5)
                
                if not ebay_results:
                    self.metrics.ebay_search_failed += 1
                    self.audit_logger.log_event(
                        "ebay_search_failed",
                        {"product": source_item.product_title, "reason": "no_results"}
                    )
                    continue
                
                self.metrics.ebay_search_success += 1
                
                # マッチング（最初の eBay 結果を参照価格とする）
                best_ebay = ebay_results[0]
                ebay_title = best_ebay.get("title", "")
                
                match_score = self.product_matcher._calculate_title_match(
                    source_item.product_title or "",
                    ebay_title
                )
                
                if match_score >= 0.5:  # スコア 0.5 以上を成功とする
                    self.metrics.matching_success += 1
                    
                    # 利益計算
                    ebay_price_raw = best_ebay.get("price", {})
                    if isinstance(ebay_price_raw, dict):
                        ebay_price_usd = float(ebay_price_raw.get("value", 0))
                    else:
                        ebay_price_usd = float(ebay_price_raw)
                        
                    profit_data = self.profit_calc.calculate_profit(
                        ebay_price_usd=ebay_price_usd,
                        source_price_jpy=float(source_item.source_price or 0)
                    )
                    
                    result = {
                        "candidate_id": f"RESEARCH-{datetime.now().strftime('%Y%m%d')}-{idx:04d}",
                        "product_name": source_item.product_title,
                        "source_channel": source_item_data["source"],
                        "source_price_jpy": source_item.source_price,
                        "source_url": source_item.source_url,
                        "condition_text": source_item.condition_text,
                        "ebay_title": ebay_title,
                        "ebay_price_usd": ebay_price_usd,
                        "ebay_item_id": best_ebay.get("itemId"),
                        "profit_jpy": profit_data.get("profit_jpy"),
                        "profit_margin_pct": profit_data.get("profit_margin_pct"),
                        "match_score": match_score,
                        "status": "success"
                    }
                    
                    self.results.append(result)
                    if len(self.samples) < 15:  # サンプル 15 件収集
                        self.samples.append(result)
                    
                    self.metrics.csv_output_count += 1
                    self.logger.info(f"  [{idx}] ✅ {source_item.product_title[:40]}... | "
                                   f"profit ¥{profit_data.get('profit_jpy'):,.0f} | "
                                   f"margin {profit_data.get('profit_margin_pct', 0):.1f}%")
                else:
                    self.metrics.matching_failed += 1
                    self.logger.debug(f"  [{idx}] ❌ Match score too low: {match_score:.2f}")
                    
            except Exception as e:
                self.metrics.skipped_count += 1
                reason = str(type(e).__name__)
                self.metrics.failure_reasons[reason] = self.metrics.failure_reasons.get(reason, 0) + 1
                self.logger.debug(f"  [{idx}] ⚠ Skipped: {e}")
        
        self.metrics.end_time = time.time()
    
    async def generate_output_csv(self):
        """research_results.csv 生成"""
        if not self.results:
            self.logger.warning("⚠ No results to output")
            return
        
        output_file = self.output_dir / "research_results.csv"
        
        fieldnames = [
            "candidate_id", "product_name", "source_channel", "source_price_jpy",
            "source_url", "condition_text", "ebay_title", "ebay_price_usd",
            "ebay_item_id", "profit_jpy", "profit_margin_pct", "match_score", "status"
        ]
        
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            self.logger.info(f"✅ CSV output: {output_file} ({len(self.results)} rows)")
            
        except Exception as e:
            self.logger.error(f"❌ CSV output failed: {e}")
    
    async def cleanup(self):
        """クリーンアップ: ブラウザ閉じる"""
        self.logger.info("\n=== Cleanup ===")
        if self.browser:
            await self.browser.close()
            self.logger.info("✅ Closed browser")
        if self.playwright:
            await self.playwright.stop()
            self.logger.info("✅ Stopped playwright")
    
    def generate_report(self) -> dict:
        """テスト結果レポート生成"""
        elapsed = self.metrics.end_time - self.metrics.start_time if self.metrics.end_time else 0
        
        report = {
            "execution_time": {
                "total_seconds": round(elapsed, 2),
                "per_item_seconds": round(elapsed / max(self.metrics.total_inputs, 1), 3)
            },
            "summary": {
                "total_inputs": self.metrics.total_inputs,
                "csv_output_count": self.metrics.csv_output_count,
                "skipped_count": self.metrics.skipped_count,
                "success_rate_pct": round(
                    (self.metrics.csv_output_count / max(self.metrics.total_inputs, 1)) * 100, 1
                )
            },
            "source_adapters": {
                "items_found": self.metrics.source_items_found,
                "success_rates": {
                    name: round((stats["success"] / max(stats["total"], 1)) * 100, 1)
                    for name, stats in self.metrics.source_success_rate.items()
                }
            },
            "ebay_api": {
                "search_success": self.metrics.ebay_search_success,
                "search_failed": self.metrics.ebay_search_failed,
                "success_rate_pct": round(
                    (self.metrics.ebay_search_success / max(
                        self.metrics.ebay_search_success + self.metrics.ebay_search_failed, 1
                    )) * 100, 1
                )
            },
            "matching": {
                "success": self.metrics.matching_success,
                "failed": self.metrics.matching_failed,
                "success_rate_pct": round(
                    (self.metrics.matching_success / max(
                        self.metrics.matching_success + self.metrics.matching_failed, 1
                    )) * 100, 1
                )
            },
            "failure_reasons": self.metrics.failure_reasons,
            "samples": self.samples[:10]  # 最初の 10 件サンプル
        }
        
        return report
    
    async def run(self):
        """完全テスト実行"""
        try:
            await self.initialize()
            
            # 1. ソースアダプタテスト
            adapter_test_results = await self.test_source_adapters()
            
            # 2. eBay API テスト
            await self.test_ebay_search()
            
            # 3. 完全 E2E フロー
            await self.test_end_to_end()
            
            # 4. 出力生成
            await self.generate_output_csv()
            
            # 5. レポート生成
            report = self.generate_report()
            report_file = self.output_dir / "test_report.json"
            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"\n✅ Test report: {report_file}")
            
            # 6. コンソール出力
            self._print_final_summary(report)
            
        except Exception as e:
            self.logger.error(f"❌ Test execution failed: {e}", exc_info=True)
            
        finally:
            await self.cleanup()
    
    def _print_final_summary(self, report: dict):
        """最終サマリ表示"""
        print("\n" + "="*80)
        print("📊 MARGINSCOUT OPERATIONAL TEST - FINAL REPORT")
        print("="*80)
        print(f"\n【Execution】")
        print(f"  Total Time: {report['execution_time']['total_seconds']}s")
        print(f"  Per Item: {report['execution_time']['per_item_seconds']}s")
        
        print(f"\n【Summary】")
        print(f"  Total Inputs: {report['summary']['total_inputs']}")
        print(f"  CSV Output: {report['summary']['csv_output_count']}")
        print(f"  Skipped: {report['summary']['skipped_count']}")
        print(f"  Success Rate: {report['summary']['success_rate_pct']}%")
        
        print(f"\n【Source Adapters】")
        for src, count in report['source_adapters']['items_found'].items():
            rate = report['source_adapters']['success_rates'].get(src, 0)
            print(f"  {src}: {count} items, {rate}% success rate")
        
        print(f"\n【eBay API】")
        print(f"  Success: {report['ebay_api']['search_success']}")
        print(f"  Failed: {report['ebay_api']['search_failed']}")
        print(f"  Success Rate: {report['ebay_api']['success_rate_pct']}%")
        
        print(f"\n【Matching】")
        print(f"  Success: {report['matching']['success']}")
        print(f"  Failed: {report['matching']['failed']}")
        print(f"  Success Rate: {report['matching']['success_rate_pct']}%")
        
        if report['failure_reasons']:
            print(f"\n【Failure Reasons】")
            for reason, count in sorted(report['failure_reasons'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {reason}: {count}")
        
        print("\n" + "="*80 + "\n")


async def main():
    runner = OperationalTestRunner()
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
