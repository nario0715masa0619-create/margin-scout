"""
Keyword extraction utilities (rule-based and AI-based).
Reused from the original eBay Research Edge.
"""

import re
import unicodedata
from typing import List
from openai import OpenAI
from src.source_adapters.config_adapters import OPENAI_API_KEY


CLIENT = OpenAI(api_key=OPENAI_API_KEY)


def extract_keywords(title: str) -> List[str]:
    """
    Extract keywords from product title using rule-based logic.
    
    Priority:
    1. Card number (e.g., "123/456")
    2. Rarity markers (SAR, SR, AR, HR, UR)
    3. Pokemon name (mapped to Japanese)
    4. Fallback: 3+ character words
    
    Args:
        title: Product title
    
    Returns:
        List[str]: Extracted keywords
    """
    kw = []
    t = unicodedata.normalize('NFKD', title).lower()
    
    # 1. Extract card number (e.g., 123/456) - PRIORITY
    m = re.search(r'(\d+/[A-Z0-9]+)', title.upper())
    card_number = m.group(1) if m else None
    
    # 2. Extract rarity (as independent word)
    rarity = None
    if re.search(r'\bsar\b', t):
        rarity = 'SAR'
    elif re.search(r'\bsr\b', t):
        rarity = 'SR'
    elif re.search(r'\bar\b', t):
        rarity = 'AR'
    elif re.search(r'\bhr\b', t):
        rarity = 'HR'
    elif re.search(r'\bur\b', t):
        rarity = 'UR'
    
    # 3. Pokemon name to Japanese mapping
    mapping = {
        'pikachu': 'ピカチュウ',
        'charizard': 'リザードン',
        'manaphy': 'マナフィ',
        'gengar': 'ゲンガー',
        'mewtwo': 'ミュウツー',
        'mew': 'ミュウ',
    }
    ja_name = None
    for en, ja in mapping.items():
        if en in t:
            ja_name = ja
            break
    
    # 4. Build search keywords
    if card_number:
        if rarity:
            kw.append(rarity)
        kw.append(card_number)
        if ja_name:
            kw.append(ja_name)
    else:
        if ja_name:
            kw.append(ja_name)
        if rarity:
            kw.append(rarity)
    
    # Fallback: extract words if no keywords yet
    if not kw:
        words = re.findall(r'[a-zA-Z0-9]{3,}', title)
        kw = words[:2]
    
    # Remove duplicates while preserving order
    kw = list(dict.fromkeys(kw))
    return kw


def extract_keywords_ai(title: str, genre: str = '') -> List[str]:
    """
    Extract keywords using OpenAI GPT.
    Optimized for Japanese flea market searches.
    
    Args:
        title: Product title (can be English eBay title)
        genre: Product genre/category
    
    Returns:
        List[str]: Extracted keywords in Japanese
    """
    try:
        if not OPENAI_API_KEY:
            print(f"[WARN] OPENAI_API_KEY not set. Using rule-based extraction.")
            return extract_keywords(title)
        
        clean_title = re.sub(r'[^\w\s]', ' ', title)
        
        prompt = f"""以下のeBayの商品名から、日本のフリマサイト（メルカリ、ヤフオク等）で検索するのに最適な「日本語のキーワード」を3〜5単語程度で抽出してください。
        
        ジャンル: {genre}
        eBay商品名: {title}
        
        [重要ルール]
        - **作品名やキャラクター名は、日本公式の「漢字表記（フルネーム）」を絶対に最優先してください（例: Isagi Yoichi -> 潔世一, Yoichi Isagi -> 潔世一）。**
        - **「イサギヨイチ」のようなカタカナ表記は、漢字が不明な場合を除き禁止します。**
        - ジャンル名も適切に日本語に変換してください（例: Figure -> フィギュア）。
        - 出力は、最も重要な単語をスペース区切りで「キーワードのみ」返してください。
        - 余計な説明や記号は一切不要です。"""
        
        r = CLIENT.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0
        )
        kw_str = r.choices[0].message.content.strip()
        kw = [k.strip() for k in kw_str.split(' ') if k.strip()]
        print(f"  [AI-KW] {title[:20]}... -> {kw}")
        return kw
    except Exception as e:
        print(f"  [AI-KW-ERR] {e}. Falling back to rule-based.")
        return extract_keywords(title)
