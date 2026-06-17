import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

print('='*70)
print('Phase B+ Step 4～6: さらに精度向上')
print('='*70)

# ============================================================
# Step 4: しきい値緩和 (0.4 → 0.35)
# ============================================================
print('\n✅ Step 4: マッチング閾値緩和 (0.4 → 0.35)')

improved_matcher_code = '''from difflib import SequenceMatcher

class ImprovedProductMatcher:
    """緩和ロジック + 段階的マッチング"""
    
    def __init__(self):
        # 緩和後の閾値
        self.thresholds = {
            'exact': 0.95,
            'strong': 0.7,
            'moderate': 0.35,  # 0.4 → 0.35 に緩和
            'weak': 0.25       # 追加: 弱い一致
        }
    
    def multi_stage_match(self, source_title, ebay_results):
        """複数段階でマッチング試行（緩和版）"""
        
        if not ebay_results:
            return None, 0.0, 'no_ebay_results'
        
        best_match = None
        best_score = 0.0
        match_stage = 'none'
        
        # Stage 1: 完全一致 (0.95以上)
        for item in ebay_results:
            score = self._jaccard_similarity(source_title.lower(), item.get('title', '').lower())
            if score >= self.thresholds['exact']:
                return item, score, 'exact_match'
        
        # Stage 2: 強い一致 (0.7～0.94)
        for item in ebay_results:
            score = self._jaccard_similarity(source_title.lower(), item.get('title', '').lower())
            if score >= self.thresholds['strong'] and score > best_score:
                best_match = item
                best_score = score
                match_stage = 'strong_match'
        
        if best_match and match_stage == 'strong_match':
            return best_match, best_score, match_stage
        
        # Stage 3: 中程度一致 (0.35～0.69) ← 緩和
        for item in ebay_results:
            score = self._jaccard_similarity(source_title.lower(), item.get('title', '').lower())
            if score >= self.thresholds['moderate'] and score > best_score:
                best_match = item
                best_score = score
                match_stage = 'moderate_match'
        
        if best_match and match_stage == 'moderate_match':
            return best_match, best_score, match_stage
        
        # Stage 4: シーケンスマッチャー (SequenceMatcher利用)
        for item in ebay_results:
            seq_score = SequenceMatcher(None, source_title.lower(), item.get('title', '').lower()).ratio()
            if seq_score >= self.thresholds['moderate'] and seq_score > best_score:
                best_match = item
                best_score = seq_score
                match_stage = 'sequence_match'
        
        # Stage 5: 弱い一致 (0.25以上) ← 追加段階
        if not best_match:
            for item in ebay_results:
                score = self._jaccard_similarity(source_title.lower(), item.get('title', '').lower())
                if score >= self.thresholds['weak'] and score > best_score:
                    best_match = item
                    best_score = score
                    match_stage = 'weak_match'
        
        if best_score >= self.thresholds['moderate']:
            return best_match, best_score, match_stage
        
        return None, 0.0, 'no_match'
    
    def _jaccard_similarity(self, s1, s2):
        """Jaccard 類似度計算"""
        set1 = set(s1.split())
        set2 = set(s2.split())
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0
'''

with open('src/research_workflow/product_matcher_improved.py', 'w', encoding='utf-8') as f:
    f.write(improved_matcher_code)

print('  ✅ 新閾値: 0.35 (0.4から緩和)')
print('  ✅ 新段階: weak_match (0.25以上) 追加')
print('  📁 ファイル: src/research_workflow/product_matcher_improved.py')

# ============================================================
# Step 5: LLM キーワード正規化 (Claude API 不要版)
# ============================================================
print('\n✅ Step 5: LLM キーワード正規化（ルールベース）')

llm_normalizer_code = '''import re

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
        normalized = re.sub(r'\\s+', ' ', normalized).strip()
        
        return normalized
    
    @classmethod
    def extract_search_query(cls, title):
        """eBay 検索向けキーワード抽出"""
        normalized = cls.normalize(title)
        
        # ブランド + 型番の抽出
        brand_pattern = r'(Nikon|Canon|Sony|Fujifilm|Gucci|Louis Vuitton|Prada)'
        model_pattern = r'(D\\d{3,4}|EOS\\s*\\d+|α\\d+|GG|Monogram)'
        
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
'''

with open('src/research_workflow/keyword_normalizer.py', 'w', encoding='utf-8') as f:
    f.write(llm_normalizer_code)

print('  ✅ 日本語 → eBay 検索向け標準形に正規化')
print('  ✅ ブランド・型番自動抽出')
print('  📁 ファイル: src/research_workflow/keyword_normalizer.py')

# ============================================================
# Step 6: eBay 検索条件詳細化
# ============================================================
print('\n✅ Step 6: eBay 検索条件詳細化（競争力商品絞込み）')

advanced_search_code = '''class AdvancedEbaySearcher:
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
'''

with open('src/research_workflow/advanced_ebay_searcher.py', 'w', encoding='utf-8') as f:
    f.write(advanced_search_code)

print('  ✅ eBay 検索条件詳細化（中古品、正評価出品者のみ）')
print('  ✅ 価格帯絞込み（¥5,000～¥200,000）')
print('  📁 ファイル: src/research_workflow/advanced_ebay_searcher.py')

print('\n' + '='*70)
print('✅ Step 4～6 実装完了')
print('='*70)
print('\n📊 改善内容サマリー:')
print('  1️⃣  マッチング閾値: 0.4 → 0.35 (ヒット率向上)')
print('  2️⃣  LLM キーワード正規化: 日本語 → eBay 標準形')
print('  3️⃣  eBay 検索条件詳細化: 競争力商品に絞込み')
print('\n次: E2E テスト再実行で効果測定')
