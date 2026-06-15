"""
Research processor with source adapter integration.
Phase E: Complete end-to-end workflow.

Flow:
  1. Read input CSV (product candidates)
  2. Search eBay Browse API for reference prices
  3. Match with ProductMatcher
  4. For each matched candidate:
     - Search Mercari
     - Search Yahoo Fleamarket
     - Get Yahoo Auction history
     - Search Hardoff
  5. Aggregate results
  6. Calculate profit (eBay price vs source prices)
  7. Output research_results.csv + listing_seed.csv
  8. Log to audit JSONL
"""

import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
import csv

from playwright.async_api import async_playwright
from src.ebay_integration import EbayBrowseApiClient, EbayAuthHandler, EbayResponseNormalizer
from src.research_workflow.product_matcher import ProductMatcher
from src.research_workflow.research_data import ResearchCandidate, ResearchStatus
from src.source_adapters import (
    MercariAdapter,
    YahooFleamarketAdapter,
    YahooAuctionHistoryAdapter,
    HardoffAdapter,
    SourceItem,
)
from src.source_adapters.utils.keywords import extract_keywords_ai, extract_keywords
from src.source_adapters.utils.currency import get_exchange_rate
from src.research_workflow.audit_logger import AuditLogger


class ResearchProcessorWithSources:
    """Complete research processor with eBay API + source adapters."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = []
        self.audit_logger = AuditLogger(output_dir)
    
    async def process_csv(self, input_csv: str, genre: str = "ポケモンカード") -> Dict[str, Any]:
        """
        Process input CSV and perform complete research workflow.
        
        Args:
            input_csv: Path to input CSV file
            genre: Product genre/category
        
        Returns:
            dict: Summary of processing
        """
        print("[PHASE-E] Starting complete E2E research workflow")
        print(f"  Input: {input_csv}")
        print(f"  Genre: {genre}")
        print()
        
        # Read input CSV
        candidates = self._read_input_csv(input_csv)
        total_input = len(candidates)
        
        print(f"[LOAD] Read {total_input} candidates from CSV")
        print()
        
        if total_input == 0:
            print("[ERROR] No candidates found in input CSV")
            return {'total_input': 0, 'successful': 0, 'skipped': 0}
        
        # Initialize eBay API
        auth_handler = EbayAuthHandler()
        token = auth_handler.get_token()
        if not token:
            print("[ERROR] Failed to get eBay token")
            return {'total_input': total_input, 'successful': 0, 'skipped': 0, 'error': 'eBay auth failed'}
        
        ebay_client = EbayBrowseApiClient(auth_handler)
        matcher = ProductMatcher()
        
        # Get exchange rate
        exchange_rate = get_exchange_rate()
        print(f"[RATE] Exchange rate: 1 USD = ¥{exchange_rate:.2f}")
        print()
        
        # Start Playwright browser
        successful = 0
        skipped = 0
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                for idx, candidate in enumerate(candidates, 1):
                    print(f"[{idx}/{total_input}] Processing: {candidate.get('product_name', 'Unknown')}")
                    
                    try:
                        # 1. Search eBay API
                        product_name = candidate.get('product_name', '')
                        ebay_items = await ebay_client.search(product_name, limit=3)
                        
                        if not ebay_items:
                            print(f"  [SKIP] No eBay items found")
                            self.audit_logger.log_error(
                                candidate.get('sku', f'row_{idx}'),
                                idx,
                                'no_ebay_match',
                                f'No eBay items found for: {product_name}'
                            )
                            skipped += 1
                            continue
                        
                        # Use best eBay match
                        ebay_item = ebay_items[0]
                        ebay_price_usd = float(ebay_item.get('price', {}).get('value', 0))
                        ebay_item_id = ebay_item.get('itemId', '')
                        
                        print(f"  [eBay] Found: {ebay_item.get('title', '')[:50]} @ ${ebay_price_usd:.2f}")
                        
                        # 2. Generate keywords
                        keywords = extract_keywords_ai(product_name, genre)
                        if not keywords:
                            keywords = extract_keywords(product_name)
                        
                        print(f"  [KW] {keywords}")
                        
                        # 3. Create page for adapters
                        page = await browser.new_page()
                        
                        # 4. Search all sources in parallel
                        try:
                            sources = await self._search_all_sources(
                                page,
                                browser,
                                keywords,
                                genre
                            )
                        finally:
                            await page.close()
                        
                        print(f"  [SOURCES] Found {len(sources)} items total")
                        
                        # 5. Calculate profit
                        ebay_price_jpy = ebay_price_usd * exchange_rate
                        
                        result = {
                            'candidate_id': f'MSCOUT-{datetime.now().strftime("%Y%m%d")}-E2E-{idx:03d}',
                            'product_name': product_name,
                            'sku': candidate.get('sku', ''),
                            'ebay_item_id': ebay_item_id,
                            'ebay_title': ebay_item.get('title', ''),
                            'ebay_price_usd': ebay_price_usd,
                            'ebay_price_jpy': ebay_price_jpy,
                            'source_items': sources,
                            'best_source': self._best_source(sources, ebay_price_jpy) if sources else None,
                            'keywords': keywords,
                            'status': 'completed',
                        }
                        
                        self.results.append(result)
                        
                        # Log success
                        self.audit_logger.log_event('process_success', {
                            'candidate_id': result['candidate_id'],
                            'product_name': product_name,
                            'ebay_items': len(ebay_items),
                            'source_items': len(sources),
                        })
                        
                        successful += 1
                        print(f"  ✓ SUCCESS")
                        print()
                        
                    except Exception as e:
                        print(f"  ✗ ERROR: {e}")
                        self.audit_logger.log_error(
                            candidate.get('sku', f'row_{idx}'),
                            idx,
                            'process_error',
                            str(e)
                        )
                        skipped += 1
                        print()
                        continue
            
            finally:
                await browser.close()
        
        # 6. Export results
        self._export_csv()
        
        # Print summary
        print("=" * 70)
        print("[SUMMARY]")
        print(f"  Total Input: {total_input}")
        print(f"  Successful: {successful}")
        print(f"  Skipped: {skipped}")
        print(f"  Output: {self.output_dir}")
        print("=" * 70)
        print()
        
        return {
            'total_input': total_input,
            'successful': successful,
            'skipped': skipped,
            'output_dir': str(self.output_dir),
        }
    
    async def _search_all_sources(self, page, browser, keywords: List[str], genre: str) -> List[Dict]:
        """
        Search all 4 sources in parallel.
        
        Returns:
            list: Aggregated SourceItem results
        """
        # Create adapters
        mercari = MercariAdapter(page)
        
        # For Yahoo and Hardoff, we need separate pages
        page_yahoo = await browser.new_page()
        yahoo_flea = YahooFleamarketAdapter(page_yahoo)
        
        yahoo_auction = YahooAuctionHistoryAdapter(browser)
        
        page_hardoff = await browser.new_page()
        hardoff = HardoffAdapter(page_hardoff)
        
        try:
            # Search in parallel
            results = await asyncio.gather(
                mercari.search(keywords, genre),
                yahoo_flea.search(keywords, genre),
                yahoo_auction.search(keywords),
                hardoff.search(keywords, genre),
                return_exceptions=True
            )
            
            # Flatten and filter exceptions
            all_items = []
            source_names = ['Mercari', 'YahooFlea', 'YahooAuction', 'Hardoff']
            
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"    [WARN] {source_names[idx]} error: {result}")
                    continue
                
                all_items.extend(result)
            
            # Convert to dict for export
            return [item.to_dict() for item in all_items]
        
        finally:
            await yahoo_flea.close()
            await page_yahoo.close()
            await page_hardoff.close()
            await hardoff.close()
    
    def _best_source(self, sources: List[Dict], ebay_price_jpy: float) -> Dict:
        """Find best (lowest) source price."""
        if not sources:
            return None
        
        best = min(sources, key=lambda x: x.get('source_price', float('inf')))
        best['profit_jpy'] = ebay_price_jpy - best.get('source_price', 0)
        best['profit_margin_pct'] = (best['profit_jpy'] / ebay_price_jpy * 100) if ebay_price_jpy > 0 else 0
        
        return best
    
    def _read_input_csv(self, csv_path: str) -> List[Dict]:
        """Read input CSV file."""
        candidates = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                candidates = list(reader)
        except Exception as e:
            print(f"[ERROR] Failed to read CSV: {e}")
        
        return candidates
    
    def _export_csv(self):
        """Export results to CSV files."""
        # Export research_results.csv
        research_csv = self.output_dir / 'research_results.csv'
        
        if self.results:
            with open(research_csv, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'candidate_id', 'product_name', 'sku', 'ebay_item_id', 'ebay_title',
                    'ebay_price_usd', 'ebay_price_jpy', 'best_source_channel',
                    'best_source_price', 'best_source_url', 'profit_jpy', 'profit_margin_pct',
                    'status'
                ])
                writer.writeheader()
                
                for result in self.results:
                    best = result.get('best_source', {})
                    writer.writerow({
                        'candidate_id': result['candidate_id'],
                        'product_name': result['product_name'],
                        'sku': result['sku'],
                        'ebay_item_id': result['ebay_item_id'],
                        'ebay_title': result['ebay_title'],
                        'ebay_price_usd': f"{result['ebay_price_usd']:.2f}",
                        'ebay_price_jpy': f"{result['ebay_price_jpy']:.0f}",
                        'best_source_channel': best.get('source_channel', ''),
                        'best_source_price': best.get('source_price', ''),
                        'best_source_url': best.get('source_url', ''),
                        'profit_jpy': f"{best.get('profit_jpy', 0):.0f}",
                        'profit_margin_pct': f"{best.get('profit_margin_pct', 0):.1f}",
                        'status': result['status'],
                    })
        
        print(f"[EXPORT] research_results.csv written")
