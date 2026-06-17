"""クエリオプティマイザ - eBay 検索用クエリの最適化"""
import re
import logging
from typing import Dict, List, Optional
from pykakasi import kakasi

class QueryOptimizer:
    """eBay 検索向けに仕入れ元商品のタイトルを最適化するクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.kks = kakasi()
        
        # 除外するノイズキーワード（フリマ特有の表現）
        self.noise_patterns = [
            r"【.*?】", r"\[.*?\]", r"＼.*?／", r"★.*?★", 
            r"美品", r"極美品", r"新品", r"未使用", r"ジャンク", 
            r"送料無料", r"送料込み", r"匿名配送", r"即購入[ok|OK|歓迎]",
            r"まとめ売り", r"セット", r"限定", r"純正", r"おまけ付き?",
            r"動作確認済[み]?"
        ]
        
        # カラーキーワード（検索から除外して純粋な型番を残すため）
        self.color_keywords = [
            "ブラック", "ホワイト", "レッド", "ブルー", "イエロー", "グリーン",
            "スペースグレイ", "シルバー", "ゴールド", "ローズゴールド", "スターライト", "ミッドナイト",
            "black", "white", "red", "blue", "yellow", "green", "silver", "gold"
        ]
        
    def _clean_title(self, title: str) -> str:
        """ノイズキーワードや記号を除去"""
        cleaned = title
        # 記号系ノイズの除去
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
        
        # 特殊記号をスペースに
        cleaned = re.sub(r"[!\"#$%&'()*+,./:;<=>?@\\^_`{|}~「」『』〜ー~]", " ", cleaned)
        
        # 重複スペースの削除
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _extract_brand(self, title: str, category: str = "") -> Optional[str]:
        """よくあるブランド名をタイトルから抽出（簡易版）"""
        # category や title から既知のブランドを抽出
        known_brands = {
            "apple": ["apple", "macbook", "iphone", "ipad", "airpods"],
            "sony": ["sony", "playstation", "ps4", "ps5", "wh-", "wf-", "alpha", "a7"],
            "nintendo": ["nintendo", "switch", "ds", "gameboy", "任天堂", "ニンテンドー"],
            "canon": ["canon", "eos", "powershot", "ixy", "キヤノン", "キャノン"],
            "nikon": ["nikon", "coolpix", "ニコン"],
            "pokemon": ["pokemon", "ポケモン"],
            "gucci": ["gucci", "グッチ"],
            "louis vuitton": ["louis vuitton", "ルイヴィトン", "ヴィトン"],
            "lego": ["lego", "レゴ"],
            "bandai": ["bandai", "バンダイ", "gunpla", "ガンプラ"]
        }
        
        lower_title = title.lower()
        for brand, keywords in known_brands.items():
            for kw in keywords:
                if kw in lower_title:
                    return brand
        return None

    def _extract_model(self, title: str) -> str:
        """型番や固有の英数字の組み合わせを抽出"""
        # 大文字小文字問わず、英字と数字が混ざった文字列、または数字を含む文字列
        # 例: "iPhone 12", "WH-1000XM4", "D300", "EOS 5D"
        tokens = title.split()
        model_parts = []
        for token in tokens:
            if re.search(r"[a-zA-Z]", token) and re.search(r"[0-9]", token):
                # 英数字混在
                model_parts.append(token)
            elif re.search(r"^[0-9]+[a-zA-Z]+$", token) or re.search(r"^[a-zA-Z]+[0-9]+$", token):
                model_parts.append(token)
            elif re.search(r"[0-9]{2,}", token):
                # 2桁以上の数字（容量や世代の可能性）
                model_parts.append(token)
            elif token.lower() in ["pro", "max", "mini", "plus", "air"]:
                # Apple系の修飾詞
                model_parts.append(token)
        
        # 英単語のみのトークンも、モデル名の一部かもしれないので拾う
        english_words = [t for t in tokens if re.match(r"^[a-zA-Z]+$", t)]
        
        # 組み合わせる（ユニークにする）
        all_parts = []
        for p in english_words + model_parts:
            if p not in all_parts and p.lower() not in self.color_keywords:
                all_parts.append(p)
                
        return " ".join(all_parts)

    def _to_romaji(self, text: str) -> str:
        """日本語をローマ字に変換"""
        result = self.kks.convert(text)
        romaji_parts = []
        for item in result:
            romaji = item['hepburn']
            if romaji:
                romaji_parts.append(romaji)
        return " ".join(romaji_parts)

    def generate_queries(self, source_product: Dict) -> List[str]:
        """
        1つの商品から、優先度順に複数のeBay検索クエリを生成する
        
        Returns:
            List[str]: 検索クエリのリスト
        """
        raw_title = source_product.get("product_name", "")
        brand_hint = source_product.get("brand", "")
        model_hint = source_product.get("model_number", "")
        
        cleaned_title = self._clean_title(raw_title)
        
        # 1. ブランドと型番が明示されている場合
        queries = []
        if brand_hint and model_hint:
            queries.append(f"{brand_hint} {model_hint}")
            
        # 2. タイトルから英語・英数字（型番・ブランド名）を抽出
        extracted_brand = self._extract_brand(cleaned_title) or brand_hint
        extracted_model = self._extract_model(cleaned_title)
        
        if extracted_model:
            # 抽出したモデル名とブランド名を組み合わせる
            if extracted_brand and extracted_brand.lower() not in extracted_model.lower():
                queries.append(f"{extracted_brand} {extracted_model}")
            else:
                queries.append(extracted_model)
                
        # 3. タイトル全体のローマ字変換（英数字はそのまま）
        # 日本語のみが含まれる場合などのフォールバック
        romaji_title = self._to_romaji(cleaned_title)
        romaji_words = romaji_title.split()
        
        # ローマ字化されたタイトルから上位4単語をクエリ化
        if romaji_words:
            top_romaji = " ".join(romaji_words[:4])
            if top_romaji not in queries:
                queries.append(top_romaji)
                
        # 重複を排除しつつ順序を維持
        seen = set()
        unique_queries = []
        for q in queries:
            q_clean = re.sub(r"\s+", " ", q).strip()
            if q_clean and len(q_clean) >= 2 and q_clean.lower() not in seen:
                unique_queries.append(q_clean)
                seen.add(q_clean.lower())
                
        # もし抽出に失敗した場合は、デフォルトを返す
        if not unique_queries:
            self.logger.warning(f"Could not generate query for: {raw_title}")
            return ["item"]
            
        return unique_queries
