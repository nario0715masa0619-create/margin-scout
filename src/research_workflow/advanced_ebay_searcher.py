class AdvancedEbaySearcher:
    """競争力のある商品に絞込むための eBay 検索パラメータ"""
    
    @staticmethod
    def build_search_params(query, category=None, condition='used'):
        """検索パラメータを構築"""
        params = {
            'q': query,
            'limit': 10,
            'sort': 'newlyListed',  # 新しい順
            'filter': []
        }
        
        # 条件フィルタ (used / new)
        if condition == 'used':
            params['filter'].append('conditions:{USED|FOR_PARTS_OR_NOT_WORKING}')
        elif condition == 'new':
            params['filter'].append('conditions:{NEW}')
        
        # 価格帯フィルタ（オプション）
        # 中古品は ¥5,000～¥200,000 に絞込み
        if condition == 'used':
            params['filter'].append('price:[5000..200000]')  # JPY
        
        # 出品者評価フィルタ
        params['filter'].append('sellers:{POSITIVE}')  # ポジティブ評価のみ
        
        # カテゴリ指定（オプション）
        if category:
            params['category'] = category
        
        return params
    
    @staticmethod
    def get_search_params_for_api(query):
        """Browse API 対応パラメータ"""
        return {
            'q': query,
            'limit': 10,
            'sort': 'newlyListed',
            'filter': 'conditions:{USED|FOR_PARTS_OR_NOT_WORKING}',
        }
