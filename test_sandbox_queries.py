import sys, asyncio
from pathlib import Path
sys.path.insert(0, str(Path('.')))
from src.ebay_integration.auth_handler import EbayAuthHandler
from src.ebay_integration.browse_api_client import EbayBrowseApiClient

async def test():
    a = EbayAuthHandler()
    c = EbayBrowseApiClient(a)
    for q in ['iPhone', 'iPhone 12', 'iPhone 12 Pro Max', 'Apple iPhone 12', 'GUCCI', 'Sony', 'Canon']:
        r = await c.search(q, limit=5)
        print(f'{q} -> {len(r)} items')
        for item in r:
            print(f'  - {item.get("title")}')

asyncio.run(test())
