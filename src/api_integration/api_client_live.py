# src/api_integration/api_client_live.py
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum
import requests

class APIErrorType(str, Enum):
    OAUTH_ERROR = "oauth_error"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMIT = "rate_limit"
    NETWORK_ERROR = "network_error"
    SERVER_ERROR = "server_error"
    PARTIAL_SUCCESS = "partial_success"
    UNKNOWN = "unknown"

@dataclass
class APIError:
    error_type: APIErrorType
    status_code: int
    message: str
    details: Dict = None
    retriable: bool = False
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    def should_retry(self) -> bool:
        return self.retriable

@dataclass
class APIResponse:
    status_code: int
    success: bool
    data: Dict
    error: Optional[APIError] = None
    raw_response: Optional[requests.Response] = None
    timestamp: str = None
    
    def __post_init__(self):
        from datetime import datetime
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class EBayLiveAPIClient:
    def __init__(self, oauth_handler, api_config):
        self.oauth_handler = oauth_handler
        self.api_config = api_config
    
    def create_inventory_item(self, sku: str, payload: Dict) -> APIResponse:
        endpoint = f'/sell/inventory/v1/inventory_item/{sku}'
        return self._make_request('PUT', endpoint, payload)
    
    def create_offer(self, payload: Dict) -> APIResponse:
        endpoint = '/sell/inventory/v1/offer'
        return self._make_request('POST', endpoint, payload)
    
    def publish_offer(self, offer_id: str) -> APIResponse:
        endpoint = f'/sell/inventory/v1/offer/{offer_id}/publish'
        return self._make_request('POST', endpoint, None)
    
    def _make_request(self, method: str, endpoint: str, payload: Optional[Dict] = None) -> APIResponse:
        try:
            access_token = self.oauth_handler.get_access_token()
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
            url = f"{self.api_config.base_url}{endpoint}"
            
            print(f"[API] {method} {endpoint}")
            
            if method == 'PUT':
                response = requests.put(url, headers=headers, json=payload, timeout=self.api_config.timeout)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=payload, timeout=self.api_config.timeout)
            else:
                response = requests.get(url, headers=headers, timeout=self.api_config.timeout)
            
            try:
                response_data = response.json()
            except:
                response_data = {'raw_text': response.text}
            
            if response.status_code >= 400:
                error = self._parse_error(response.status_code, response_data)
                return APIResponse(
                    status_code=response.status_code,
                    success=False,
                    data=response_data,
                    error=error,
                    raw_response=response,
                )
            
            return APIResponse(
                status_code=response.status_code,
                success=True,
                data=response_data,
                raw_response=response,
            )
        
        except requests.RequestException as e:
            error = APIError(
                error_type=APIErrorType.NETWORK_ERROR,
                status_code=0,
                message=str(e),
                retriable=True,
            )
            return APIResponse(
                status_code=0,
                success=False,
                data={},
                error=error,
            )
    
    def _parse_error(self, status_code: int, response_data: Dict) -> APIError:
        if status_code == 401:
            return APIError(
                error_type=APIErrorType.OAUTH_ERROR,
                status_code=status_code,
                message='Unauthorized. Token may be expired.',
                retriable=True,
            )
        elif status_code == 429:
            return APIError(
                error_type=APIErrorType.RATE_LIMIT,
                status_code=status_code,
                message='Rate limited. Retry after backoff.',
                retriable=True,
            )
        elif status_code in [400, 404]:
            return APIError(
                error_type=APIErrorType.VALIDATION_ERROR,
                status_code=status_code,
                message=response_data.get('message', 'Validation error'),
                details=response_data,
                retriable=False,
            )
        elif status_code >= 500:
            return APIError(
                error_type=APIErrorType.SERVER_ERROR,
                status_code=status_code,
                message='eBay API server error',
                retriable=True,
            )
        else:
            return APIError(
                error_type=APIErrorType.UNKNOWN,
                status_code=status_code,
                message=response_data.get('message', 'Unknown error'),
                details=response_data,
            )
