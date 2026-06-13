# Listing to Payload Mapping Reference

Date: 2026-06-13

## Column Mapping: ListingReadyRecord → ExecutionPayload

| ListingReadyRecord Field | ExecutionPayload Field | Transformation | Notes |
| --- | --- | --- | --- |
| title | title | Direct | Validated for length (≤ 80 chars) |
| description | description | HTML escape | Remove raw HTML tags |
| sku | sku | Direct | Format: MARGIN-YYYYMMDD-NNNN |
| category | ebay_category_id | Category lookup | Resolve to eBay ID (with fallback) |
| category | ebay_category_path | Category path | Full path in eBay tree |
| condition | condition_ebay_enum | Condition mapping | Map to eBay enum (3000/7000) |
| price | price | Price calculation | Apply margin & fee strategy |
| quantity | quantity | Direct | Default: 1 |
| images | pictures | Path resolution | Resolve from data/images/{SKU}/ |
| candidate_id | candidate_id | Direct | For audit trail |
| source_url | source_url | Direct | For audit trail |
| user_notes | user_notes | Direct | For audit trail |
| user_tags | user_tags | Direct | For audit trail (optional) |
| (new) | reference_price | From research | Used for price calculation |
| (new) | margin_policy | Config | Policy percentage |
| (new) | platform_fees | Config | eBay FVF percentage |

## Price Calculation Transformation
- Input: reference_price, margin_policy, platform_fees
- Formula: `price = reference_price / (1 - margin% - fee%)`
- Output: price (float, 2 decimals)

## Category Resolution Transformation
- Input: Internal category string (e.g., "Electronics > Cameras > Lenses")
- Process: Lookup in eBay Category Tree mapping table
- Output: ebay_category_id (int), ebay_category_path (string)

## Condition Mapping Transformation
- Input: Internal condition enum
- Output: condition_ebay_enum (int, 3000 or 7000)

## Image Path Resolution Transformation
- Input: SKU
- Process: Construct directory path: data/images/{SKU}/
- Output: pictures (list of file paths)

## Validation Transformation
- Input: All transformed fields
- Process: Check title length, description length, price bounds, category validity
- Output: validation_report (dict with errors/warnings/score)

## Audit Trail Transformation
- Input: candidate_id, source_url, user_notes, reference_price, calculated_price, etc.
- Process: Package audit fields into audit record for traceability
- Output: audit (dict with all traceability info)
