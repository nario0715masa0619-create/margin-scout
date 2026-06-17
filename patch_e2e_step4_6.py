import re

with open('test_operational_multicat_nonmock.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace imports
content = content.replace(
    "from src.research_workflow.product_matcher_advanced import AdvancedProductMatcher",
    "from src.research_workflow.product_matcher_improved import ImprovedProductMatcher as AdvancedProductMatcher"
)

# Insert new imports for KeywordNormalizer and AdvancedEbaySearcher
if "KeywordNormalizer" not in content:
    content = content.replace(
        "from src.research_workflow.csv_handler_advanced import AdvancedCsvHandler",
        "from src.research_workflow.csv_handler_advanced import AdvancedCsvHandler\nfrom src.research_workflow.keyword_normalizer import KeywordNormalizer\nfrom src.research_workflow.advanced_ebay_searcher import AdvancedEbaySearcher"
    )

# Replace query generation
# We want to extract search query using KeywordNormalizer, and use that as the basis for AdvancedQueryOptimizer, or just use KeywordNormalizer directly.
# Wait, KeywordNormalizer.extract_search_query(title) returns a single string. AdvancedQueryOptimizer.generate_fallback_queries(title) returns a list.
# Let's replace the generate_fallback_queries call to normalize the title first.
old_query = "queries = self.query_optimizer.generate_fallback_queries(source_item.product_title or keyword)"
new_query = """normalized_title = KeywordNormalizer.normalize(source_item.product_title or keyword)
                search_q = KeywordNormalizer.extract_search_query(source_item.product_title or keyword)
                queries = [search_q] + self.query_optimizer.generate_fallback_queries(normalized_title)
                # Remove duplicates while preserving order
                queries = list(dict.fromkeys(queries))"""
content = content.replace(old_query, new_query)

# Replace search to include advanced parameters
old_search = "ebay_results = await self.ebay_client.search(q, limit=5)"
new_search = """search_params = AdvancedEbaySearcher.get_search_params_for_api(q)
                    # The mock search doesn't accept full dict unpacking easily if it only expects q and limit in test mode, 
                    # but we are in live mode. Let's just pass the filter parameter.
                    ebay_results = await self.ebay_client.search(q, limit=10, **{'filter': search_params.get('filter')})"""
content = content.replace(old_search, new_search)

# Replace matcher threshold logic if it was hardcoded
content = content.replace(
    "if best_ebay and match_score >= 0.4:",
    "if best_ebay and match_score >= 0.35:  # 緩和された閾値 0.35"
)

with open('test_operational_multicat_nonmock.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch applied to test_operational_multicat_nonmock.py for Step 4-6.")
