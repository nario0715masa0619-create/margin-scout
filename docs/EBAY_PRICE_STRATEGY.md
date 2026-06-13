# eBay Price Strategy Model

Date: 2026-06-13

## Overview
The price strategy transforms a reference price (from research) into a final eBay listing price by applying margin policy and accounting for eBay platform fees.

## Price Calculation Formula
`eBay Price = Reference Price / (1 - Margin % - Platform Fee %)`

## Components
- Reference Price: The price observed from research (e.g., competitor, MSRP)
- Margin %: Desired profit margin (default 15%)
- Platform Fee %: eBay Final Value Fee (FVF, typically 12.9% for most categories)

## Example Calculation
- Reference Price: $100.00
- Margin %: 15%
- Platform Fee %: 12.9%
- Divisor: 1 - 0.15 - 0.129 = 0.721
- eBay Price: $100.00 / 0.721 = $138.69

## Rounding
- Round to nearest $0.01
- Always round up (ceiling) if fractional cents remain

## Price Bounds
- Minimum: $0.99
- Maximum: $999,999.99
- Validation: Reject if eBay Price falls outside bounds

## Price Policy Options (Future)
- Fixed Margin (Current): Apply fixed margin % to all items
- Dynamic Margin: Adjust margin based on category, condition, demand
- Competitive Pricing: Auto-adjust to match competitor prices
- Psychological Pricing: Round to .99 or .95 for appeal

## Configuration
```json
{
  "price_strategy": "fixed_margin",
  "default_margin_percent": 15.0,
  "platform_fee_percent": 12.9,
  "min_price": 0.99,
  "max_price": 999999.99,
  "rounding_rule": "ceiling_to_nearest_cent"
}
```

## Validation Rules
- Reference price must be ≥ $0.99
- Calculated price must be ≤ $999,999.99
- Calculated price must be > reference price (margin > 0)
- Margin % must be between 0% and 95%
- Platform fee % must be between 0% and 50%
