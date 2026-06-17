import pandas as pd
from datetime import datetime

class AdvancedCsvHandler:
    """赤字商品も含めた CSV 出力"""
    
    @staticmethod
    def export_with_flags(data, output_path):
        """赤字商品・警告フラグ付き CSV 出力"""
        
        df = pd.DataFrame(data)
        
        # 利益フラグ
        df['profit_flag'] = df['profit_amount_jpy'].apply(
            lambda x: '🟢 黒字' if x > 0 else '🔴 赤字' if x < 0 else '⚪ 中立'
        )
        
        # 利益率警告
        df['margin_warning'] = df['profit_margin_pct'].abs() < 5
        df['warning_flag'] = df['margin_warning'].apply(
            lambda x: '⚠️ 低利益' if x else ''
        )
        
        # 価格差警告
        df['price_gap_warning'] = (df['ebay_price_usd'] * 157.5) / df['source_price_jpy'] if 'ebay_price_usd' in df.columns else 0
        df['price_gap_flag'] = df['price_gap_warning'].apply(
            lambda x: '⚠️ 価格差注意' if x < 1.2 else ''
        )
        
        # 出力列の順序を調整
        output_cols = [
            'source', 'product_name', 'source_price_jpy', 
            'ebay_price_usd', 'profit_amount_jpy', 'profit_margin_pct',
            'profit_flag', 'warning_flag', 'price_gap_flag',
            'match_score', 'match_stage',
            'ebay_item_id', 'ebay_url', 'timestamp'
        ]
        
        # 存在する列のみ出力
        output_cols = [col for col in output_cols if col in df.columns]
        df_output = df[output_cols]
        
        df_output.to_csv(output_path, index=False, encoding='utf-8-sig')
        return len(df_output)
