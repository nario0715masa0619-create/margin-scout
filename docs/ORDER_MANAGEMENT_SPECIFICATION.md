# Phase 7: Order Management Specification

**Date:** 2026-06-13

## Overview

Order management handles polling, parsing, and syncing eBay orders back to MarginScout's internal database.

## Order Polling Flow

1. **Query eBay Orders API** – Get new orders since last poll
2. **Parse Order Data** – Extract order_id, sku, price, buyer, etc.
3. **Match to Candidate** – Link order to original candidate
4. **Update Inventory** – Mark candidate as 'sold'
5. **Record Order** – Store order details for reporting
6. **Handle Errors** – Log failures, retry as needed

## Order Attributes

- order_id: Unique eBay order identifier
- order_status: completed / cancelled / returned
- purchase_price: Actual sale price
- quantity: Number of items in order
- buyer_username: eBay buyer username
- purchase_date: When order was placed
- shipping_address: Delivery address
- tracking_number: Shipping tracking (if available)
- order_total: Total including shipping/tax
- items: List of items in order

## Returns Management

When a return is requested:

1. Query eBay Returns API
2. Get return_id and reason
3. Update candidate status to 'returned'
4. Deduct refund from profit
5. Log return details

## Sales Reporting

Daily reports include:

- Total items sold
- Total revenue
- Total profit (revenue - cost - fees)
- Average profit margin
- Top/bottom performers by SKU
- Category breakdown
