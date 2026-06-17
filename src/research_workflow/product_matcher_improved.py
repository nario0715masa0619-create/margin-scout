from difflib import SequenceMatcher

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
