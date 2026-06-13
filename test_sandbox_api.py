import os, json, requests
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class LiveListingResult:
    sku: str
    status: str
    inventory_item_id: str = None
    offer_id: str = None
    listing_id: str = None
    item_url: str = None
    errors: list = None
    timestamp: str = None
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class EBayLiveAPIClient:
    def __init__(self, user_token):
        self.user_token = user_token
        self.base_url = 'https://api.sandbox.ebay.com'
    
    def _get_headers(self):
        return {
            'Authorization': f'Bearer {self.user_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Content-Language': 'en-US',
        }
    
    def create_inventory_item(self, sku, product_data):
        print(f'\n  [Inventory] Creating inventory item for SKU: {sku}')
        url = f'{self.base_url}/sell/inventory/v1/inventory_item/{sku}'
        
        payload = {
            'product': {
                'title': product_data.get('title', 'Product'),
                'description': product_data.get('description', 'Description'),
            },
            'condition': 'NEW',
            'availability': {
                'quantity': 10
            }
        }
        
        try:
            print(f'    URL: {url}')
            print(f'    Payload: {json.dumps(payload, indent=2)}')
            response = requests.put(url, headers=self._get_headers(), json=payload, timeout=30)
            print(f'    HTTP Status: {response.status_code}')
            
            if response.status_code in [200, 201, 204]:
                print(f'    OK: Inventory item created')
                return {'status': 'SUCCESS', 'sku': sku}
            else:
                error_msg = response.text if response.text else f'HTTP {response.status_code}'
                print(f'    ERROR: {error_msg}')
                return {'status': 'FAILED', 'error': error_msg, 'status_code': response.status_code}
        except Exception as e:
            print(f'    ERROR: {e}')
            return {'status': 'ERROR', 'error': str(e)}

env_path = os.path.expanduser('~/.marginscount/.env')
config = {}
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                config[key] = value

user_token = config.get('EBAY_REFRESH_TOKEN')
if not user_token:
    print('ERROR: EBAY_REFRESH_TOKEN not set')
    exit(1)

client = EBayLiveAPIClient(user_token)
sku = f'MARGIN-SANDBOX-{datetime.now().strftime("%Y%m%d%H%M%S")}-001'
result = client.create_inventory_item(sku, {'title': 'Test Product', 'description': 'Test'})
print(f'\nResult: {json.dumps(result, indent=2)}')
