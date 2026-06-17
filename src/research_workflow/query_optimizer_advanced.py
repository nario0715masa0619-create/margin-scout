import re
from pykakasi import kakasi

class AdvancedQueryOptimizer:
    """マルチレベルクエリ生成戦略"""
    
    def __init__(self):
        self.kks = kakasi()
    
    def generate_fallback_queries(self, title):
        """複数段階のフォールバッククエリ生成"""
        queries = []
        
        # Level 1: ブランド + 型番抽出
        brand_model = self.extract_brand_model(title)
        if brand_model:
            queries.append(brand_model)
        
        # Level 2: ブランド + 型番 (分離)
        brand = self.extract_brand(title)
        model = self.extract_model(title)
        if brand and model:
            queries.append(f"{brand} {model}")
        
        # Level 3: 型番のみ
        if model:
            queries.append(model)
        
        # Level 4: ローマ字変換
        romaji = self.romanize_title(title)
        if romaji and romaji != title:
            queries.append(romaji)
        
        # Level 5: キーワード抽出
        keywords = self.extract_keywords(title)
        if keywords:
            queries.append(" ".join(keywords[:3]))
        
        # 重複排除 & 空文字列排除
        return list(dict.fromkeys([q for q in queries if q and len(q) > 2]))
    
    def romanize_title(self, title):
        """日本語をローマ字に変換"""
        try:
            result = self.kks.convert(title)
            return "".join([item['roma'] for item in result])
        except:
            return title
    
    def extract_brand(self, title):
        """ブランド名抽出"""
        brands = ['Canon', 'Nikon', 'Sony', 'Fujifilm', 'Gucci', 'Louis Vuitton', 'Prada', 'Hermes']
        for brand in brands:
            if brand.lower() in title.lower():
                return brand
        return None
    
    def extract_model(self, title):
        """型番・モデル名抽出"""
        patterns = [r'\b[A-Z]\d+[A-Z]?\b', r'\bD\d{3,4}\b', r'\bEOS\s*\d+', r'\bα\d+']
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extract_brand_model(self, title):
        """ブランド＋型番を抽出"""
        brand = self.extract_brand(title)
        model = self.extract_model(title)
        if brand and model:
            return f"{brand} {model}"
        return None
    
    def extract_keywords(self, title):
        """重要キーワード抽出"""
        # 日本語を除去してキーワード抽出
        english_words = re.findall(r'\b[A-Za-z]{3,}\b', title)
        return english_words if english_words else [title[:20]]
