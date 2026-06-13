# eBay Live API Specification

Date: 2026-06-13

## Endpoints Used

### 1. Create Inventory Item
- Method: PUT
- Endpoint: `/sell/inventory/v1/inventory_item/{sku}`
- Purpose: Create a draft inventory item

### 2. Create Offer
- Method: POST
- Endpoint: `/sell/inventory/v1/offer`
- Purpose: Create a draft offer (pricing, policies)

### 3. Publish Offer
- Method: POST
- Endpoint: `/sell/inventory/v1/offer/{offerId}/publish`
- Purpose: Publish offer to create live listing

## Request/Response Examples
See `examples/ebay_live_api_response_sample.json`

## Error Response Format
```json
{
  "errors": [
    {
      "errorId": 25001,
      "domain": "API_INVENTORY",
      "category": "REQUEST",
      "message": "Invalid SKU",
      "longMessage": "The SKU provided is invalid or already exists"
    }
  ]
}
```

## Rate Limiting
- Calls per Minute: 60 (typical)
- Header: `X-RateLimit-Remaining`
- Action: Implement backoff when limit approached
