"""MarginScout Research Workflow Processor (実装版)"""
from datetime import datetime
from typing import List, Dict, Optional
from .normalizer import ProductNormalizer
from .category_mapper import CategoryMapper
from .price_analyzer import PriceAnalyzer
from .profit_evaluator import ProfitEvaluator
from .csv_handler import CSVHandler
from .audit_logger import AuditLogger

class ResearchWorkflowProcessor:
    """リサーチワークフロー処理エンジン（実装版）"""
    
    def __init__(self, output_dir: str = 'output'):
        self.output_dir = output_dir
        self.audit_logger = AuditLogger('logs')
        self.candidates = []
        self.results = []
    
    def process(self, input_csv: str) -> Dict:
        """メイン処理フロー"""
        # 入力を読む
        try:
            records = CSVHandler.read_input_csv(input_csv)
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
        
        self.audit_logger.stats['total_input'] = len(records)
        
        for idx, record in enumerate(records):
            result = self._process_record(record, idx + 1) # 1-indexed for row tracking
            if result:
                self.results.append(result)
                self.audit_logger.stats['successful'] += 1
                self.audit_logger.log_event('process_success', {'sku': result['sku']})
            else:
                self.audit_logger.stats['skipped'] += 1
        
        # 出力
        self._export_results()
        
        return {
            'status': 'SUCCESS',
            'summary': self.get_detailed_summary()
        }
    
    def _process_record(self, record: Dict, row_index: int) -> Optional[Dict]:
        """単一レコード処理（不正データはスキップ・ログ記録）"""
        try:
            # SKU検証
            sku = record.get('sku', '').strip()
            if not sku:
                raise ValueError("SKU is empty")
            
            # 価格検証（ここで落とす）
            retail_price_str = record.get('retail_price', '').strip()
            is_valid, retail_price, error_msg = ProductNormalizer.validate_price(retail_price_str)
            
            if not is_valid:
                raise ValueError(f"Price validation failed: {error_msg}")
            
            # 正規化
            product_name = ProductNormalizer.normalize_product_name(record.get('product_name', ''))
            
            category = record.get('category', 'default')
            quantity = int(record.get('quantity', '1'))
            
            # カテゴリマッピング
            ebay_category_id, mapping_type = CategoryMapper.map_to_ebay_category(category)
            
            # 参考価格分析
            ebay_price = PriceAnalyzer.estimate_ebay_price(retail_price)
            shipping = PriceAnalyzer.estimate_shipping_cost(ebay_price)
            
            # 利益率計算
            profit_margin = ProfitEvaluator.calculate_profit_margin(
                retail_price, ebay_price, shipping
            )
            recommendation, risk = ProfitEvaluator.evaluate_recommendation(profit_margin)
            
            # リサーチ結果
            research_id = f"MSCOUT-{datetime.now().strftime('%Y%m%d')}-{sku[-6:]}"
            
            result = {
                'research_id': research_id,
                'sku': sku,
                'product_name': product_name,
                'category_reference': category,
                'ebay_category_id': ebay_category_id,
                'retail_price_jpy': retail_price,
                'quantity_available': quantity,
                'ebay_market_price_usd': ebay_price,
                'estimated_price_usd': ebay_price,
                'shipping_cost_usd': shipping,
                'estimated_profit_usd': ebay_price - shipping - retail_price,
                'profit_margin_percent': profit_margin,
                'risk_level': risk,
                'recommendation': recommendation,
                'timestamp': datetime.now().isoformat(),
            }
            
            return result
        
        except Exception as e:
            # エラー時はNoneを返す → スキップ扱い
            self.audit_logger.log_error(
                sku=record.get('sku', 'UNKNOWN'),
                row_index=row_index,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            return None
    
    def _export_results(self) -> None:
        """結果をCSVにエクスポート"""
        import os
        os.makedirs(self.output_dir, exist_ok=True)
        CSVHandler.write_results_csv(
            f'{self.output_dir}/research_results.csv',
            self.results
        )
        
        CSVHandler.write_listing_seed_csv(
            f'{self.output_dir}/listing_seed.csv',
            self.results
        )
        
    def get_detailed_summary(self) -> Dict:
        """詳細サマリー生成"""
        return {
            'timestamp': self.audit_logger.timestamp,
            'total_input': self.audit_logger.stats['total_input'],
            'successful': self.audit_logger.stats['successful'],
            'skipped': self.audit_logger.stats['skipped'],
            'error_details': self.audit_logger.get_error_details(),
            'output_files': {
                'research_results': f'{self.output_dir}/research_results.csv',
                'listing_seed': f'{self.output_dir}/listing_seed.csv',
                'audit_log': str(self.audit_logger.log_path),
            }
        }
