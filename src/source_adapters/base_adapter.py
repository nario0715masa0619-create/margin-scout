"""
Base adapter class for all source scrapers.
Defines the common interface and data structures.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class SourceItem:
    """Common structure for items from any source."""
    source_channel: str              # 'メルカリ', 'ヤフーフリマ', 'ハードオフ' 等
    source_url: str
    source_price: int                # JPY
    source_currency: str = 'JPY'
    condition_text: str = 'unknown'  # 新品、未使用、良好 等
    product_title: str = ''
    product_image_url: str = ''
    observed_at: Optional[str] = None  # ISO 8601

    def to_dict(self):
        """Convert to dict for CSV output."""
        return {
            'source_channel': self.source_channel,
            'source_url': self.source_url,
            'source_price': self.source_price,
            'source_currency': self.source_currency,
            'condition_text': self.condition_text,
            'product_title': self.product_title,
            'product_image_url': self.product_image_url,
            'observed_at': self.observed_at or datetime.now().isoformat()
        }

class BaseSourceAdapter(ABC):
    """Base class for all source adapters."""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def search(self, keywords: List[str], genre: str = '') -> List[SourceItem]:
        """
        Search by keywords and return list of SourceItem.
        
        Args:
            keywords: List of search keywords (preferably Japanese)
            genre: Product category/genre (optional)
        
        Returns:
            List[SourceItem]: Matched items from this source
        
        Raises:
            Exception: If search fails
        """
        pass
    
    async def close(self):
        """Release resources (browser, connections, etc.)."""
        pass
