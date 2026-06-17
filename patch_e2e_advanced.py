import re

with open('test_operational_multicat_nonmock.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports
content = content.replace(
    "from src.research_workflow.product_matcher import ProductMatcher\nfrom src.research_workflow.query_optimizer import QueryOptimizer",
    "from src.research_workflow.product_matcher_advanced import AdvancedProductMatcher\nfrom src.research_workflow.query_optimizer_advanced import AdvancedQueryOptimizer\nfrom src.research_workflow.csv_handler_advanced import AdvancedCsvHandler"
)

# 2. Update instantiations
content = content.replace(
    "self.query_optimizer = QueryOptimizer()",
    "self.query_optimizer = AdvancedQueryOptimizer()"
)
content = content.replace(
    "self.product_matcher = ProductMatcher()",
    "self.product_matcher = AdvancedProductMatcher()"
)

# 3. Update query optimizer usage
old_query_opt = """                queries = self.query_optimizer.generate_queries({
                    "product_name": source_item.product_title or keyword,
                    "brand": source_item_data.get("brand", ""),
                    "model_number": source_item_data.get("model", "")
                })"""
new_query_opt = """                queries = self.query_optimizer.generate_fallback_queries(source_item.product_title or keyword)"""
content = content.replace(old_query_opt, new_query_opt)

# 4. Update product matcher usage
old_matcher = """                best_ebay, match_score = self.product_matcher.match_items(
                    source_product={"product_name": source_item.product_title or keyword},
                    ebay_search_results=ebay_results,
                    source_price_jpy=source_price
                )"""
new_matcher = """                best_ebay, match_score, match_stage = self.product_matcher.multi_stage_match(
                    source_title=source_item.product_title or keyword,
                    ebay_results=ebay_results
                )"""
content = content.replace(old_matcher, new_matcher)

# 5. Update result dict construction to include match_stage and warning_flags (profit_amount_jpy is used by AdvancedCsvHandler)
old_result_append = """                    result = {
                        "candidate_id": f"RESEARCH-{datetime.now().strftime('%Y%m%d')}-{idx:04d}",
                        "product_name": source_item.product_title or keyword,
                        "source_channel": source_item.platform,
                        "source_url": source_item.url,
                        "source_price_jpy": source_price,
                        "ebay_price_usd": ebay_price_usd,
                        "condition_text": best_ebay.get("condition"),
                        "estimated_profit_jpy": profit_data.get("profit_jpy", 0),
                        "profit_margin_pct": profit_data.get("margin_pct", 0),
                        "shipping_cost_jpy": profit_data.get("shipping_cost_jpy", 0),
                        "ebay_fees_jpy": profit_data.get("fees_jpy", 0)
                    }"""
new_result_append = """                    result = {
                        "candidate_id": f"RESEARCH-{datetime.now().strftime('%Y%m%d')}-{idx:04d}",
                        "product_name": source_item.product_title or keyword,
                        "source": source_item.platform,
                        "source_url": source_item.url,
                        "source_price_jpy": source_price,
                        "ebay_price_usd": ebay_price_usd,
                        "profit_amount_jpy": profit_data.get("profit_jpy", 0),
                        "profit_margin_pct": profit_data.get("margin_pct", 0),
                        "match_score": match_score,
                        "match_stage": match_stage,
                        "ebay_item_id": best_ebay.get("itemId", ""),
                        "ebay_url": best_ebay.get("itemWebUrl", ""),
                        "timestamp": datetime.now().isoformat()
                    }"""
content = content.replace(old_result_append, new_result_append)

# 6. Update generate_output_csv
old_generate_csv = """    async def generate_output_csv(self):
        \"\"\"research_results.csv を出力\"\"\"
        if not self.results:
            self.logger.warning("⚠️ No results to output")
            return
        
        output_file = self.output_dir / "research_results.csv"
        
        fieldnames = [
            "candidate_id", "product_name", "source_channel", "source_url", 
            "source_price_jpy", "ebay_price_usd", "condition_text", 
            "estimated_profit_jpy", "profit_margin_pct", "shipping_cost_jpy", "ebay_fees_jpy"
        ]
        
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            self.logger.info(f"✅ CSV output: {output_file} ({len(self.results)} rows)")
            
        except Exception as e:
            self.logger.error(f"❌ CSV output failed: {e}")"""
            
new_generate_csv = """    async def generate_output_csv(self):
        \"\"\"research_results.csv を出力\"\"\"
        if not self.results:
            self.logger.warning("⚠️ No results to output")
            return
        
        output_file = self.output_dir / "research_results.csv"
        
        try:
            AdvancedCsvHandler.export_with_flags(self.results, output_file)
            self.logger.info(f"✅ CSV output: {output_file} ({len(self.results)} rows)")
            
        except Exception as e:
            self.logger.error(f"❌ CSV output failed: {e}")"""

content = content.replace(old_generate_csv, new_generate_csv)

with open('test_operational_multicat_nonmock.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied to test_operational_multicat_nonmock.py successfully.")
