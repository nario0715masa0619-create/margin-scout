import re

class KeywordNormalizer:
    """日本語表現 → eBay 検索向け標準形に正規化"""
    
    NORMALIZATION_RULES = {
        # カメラ関連
        r'(デジタル)?一眼レフ|DSLR|一眼': 'DSLR',
        r'ミラーレス|mirrorless': 'Mirrorless',
        r'コンパクト|compact': 'Compact Camera',
        
        # 条件
        r'新品|新|未使用|未開封': 'new',
        r'中古|used|ジャンク': 'used',
        r'美品|良好|状態良': 'very good',
        
        # ブランド統一
        r'ニコン|Nikon': 'Nikon',
        r'キャノン|Canon': 'Canon',
        r'ソニー|Sony': 'Sony',
        r'フジフイルム|Fujifilm': 'Fujifilm',
        
        # ファッション
        r'グッチ|GUCCI': 'Gucci',
        r'ルイヴィトン|LOUIS VUITTON|LV': 'Louis Vuitton',
        r'プラダ|PRADA': 'Prada',
        
        # ホビー
        r'遊戯王|yugioh|Yu-Gi-Oh': 'Yu-Gi-Oh',
        r'ポケモン|pokemon': 'Pokemon',
        r'ワンピース|One Piece': 'One Piece',
    }
    
    @classmethod
    def normalize(cls, title):
        """タイトル正規化"""
        normalized = title
        
        for pattern, replacement in cls.NORMALIZATION_RULES.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # 重複スペース削除
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    @classmethod
    def extract_search_query(cls, title):
        """eBay 検索向けキーワード抽出"""
        normalized = cls.normalize(title)
        
        # ブランド + 型番の抽出
        brand_pattern = r'(Nikon|Canon|Sony|Fujifilm|Gucci|Louis Vuitton|Prada)'
        model_pattern = r'(D\d{3,4}|EOS\s*\d+|α\d+|GG|Monogram)'
        
        brand_match = re.search(brand_pattern, normalized)
        model_match = re.search(model_pattern, normalized)
        
        if brand_match and model_match:
            return f"{brand_match.group(1)} {model_match.group(1)}"
        elif brand_match:
            return brand_match.group(1)
        elif model_match:
            return model_match.group(1)
        
        # フォールバック: 最初の 3 単語
        words = normalized.split()
        return " ".join(words[:3]) if words else normalized
