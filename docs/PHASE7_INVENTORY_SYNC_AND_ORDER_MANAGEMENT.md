# Phase 7: Inventory Sync & Order Management

**Date:** 2026-06-13  
**Status:** Design Phase  
**Target:** Track sold items, manage inventory, handle returns

## Overview

Phase 7 implements real-time inventory synchronization with eBay and order management. After Phase 6 creates live listings, MarginScout needs to:

1. Poll eBay for sold items
2. Update internal candidate status to 'sold'
3. Track order information
4. Handle returns and cancellations
5. Generate sales reports

### Key Responsibilities

1. **Order Polling** – Query eBay Orders API for new sales
2. **Inventory Update** – Sync sold status back to internal database
3. **Returns Management** – Handle return requests
4. **Sales Tracking** – Record revenue and profit
5. **Analytics** – Generate seller metrics

---

## Phase 7 Architecture

### Order Management Flow

```
[eBay Marketplace]
    ↓
[eBay Orders API]
    ↓
[Order Poller] (scheduled)
    ↓
[Order Parser]
    ↓
[Inventory Updater]
    ↓
[Internal Database]
    ↓
[Sales Report Generator]
```

### Data Model

**Order Record:**
- order_id (eBay order ID)
- listing_id (from Phase 6)
- sku (MarginScout SKU)
- buyer_username
- order_status (completed / cancelled / returned)
- purchase_price
- quantity
- purchase_date
- shipping_address
- tracking_number (if available)
- order_total
- transaction_id

**Inventory Status:**
- sku
- candidate_id
- status (research → listed → sold → returned/cancelled)
- listing_id
- order_id (if sold)
- sold_price
- sold_date
- profit_margin
- net_income

---

## Phase 7 Endpoints

### eBay Orders API

**Get Orders:**
- GET /sell/fulfillment/v1/order
- Filters: status, date range
- Response: order list with details

**Get Order Details:**
- GET /sell/fulfillment/v1/order/{order_id}
- Response: complete order information

**Get Returns:**
- GET /sell/returns_management/v1/return
- Filters: status, date range
- Response: return requests

---

## Implementation Components

### 1. Order Poller
- Scheduled task (hourly / daily)
- Query eBay Orders API
- Detect new orders since last poll
- Handle pagination

### 2. Order Parser
- Parse eBay order response
- Extract relevant fields
- Map to internal schema
- Validate data

### 3. Inventory Updater
- Find candidate by listing_id or sku
- Update status to 'sold'
- Record order_id, sold_price, sold_date
- Calculate profit_margin and net_income

### 4. Returns Manager
- Monitor return requests
- Update status to 'returned' if applicable
- Deduct from inventory
- Track return reason

### 5. Sales Reporter
- Generate daily/weekly/monthly reports
- Calculate total revenue
- Calculate total profit
- Track high/low performers

---

## Database Schema (Proposed)

### candidates table (updated)
```sql
ALTER TABLE candidates ADD COLUMN (
  status VARCHAR(50) DEFAULT 'research',  -- research/listed/sold/returned/cancelled
  listing_id BIGINT,
  order_id VARCHAR(100),
  sold_price DECIMAL(10,2),
  sold_date TIMESTAMP,
  profit_margin DECIMAL(5,2),
  net_income DECIMAL(10,2),
  return_status VARCHAR(50),
  return_reason VARCHAR(500)
);
```

### orders table (new)
```sql
CREATE TABLE orders (
  order_id VARCHAR(100) PRIMARY KEY,
  sku VARCHAR(50),
  candidate_id VARCHAR(100),
  listing_id BIGINT,
  buyer_username VARCHAR(100),
  order_status VARCHAR(50),
  purchase_price DECIMAL(10,2),
  quantity INT,
  purchase_date TIMESTAMP,
  shipping_address TEXT,
  tracking_number VARCHAR(100),
  order_total DECIMAL(10,2),
  transaction_id VARCHAR(100),
  synced_at TIMESTAMP DEFAULT NOW(),
  FOREIGN KEY (candidate_id) REFERENCES candidates(candidate_id)
);
```

### sales_report table (new)
```sql
CREATE TABLE sales_reports (
  report_date DATE,
  total_sold INT,
  total_revenue DECIMAL(15,2),
  total_profit DECIMAL(15,2),
  avg_profit_margin DECIMAL(5,2),
  top_product_sku VARCHAR(50),
  generated_at TIMESTAMP DEFAULT NOW()
);
```

---

## Integration with Phase 6

Phase 7 **depends on** Phase 6 output:

- listing_id: Used to match orders from eBay
- sku: Internal identifier for tracking
- candidate_id: Link back to research

Phase 7 **updates** Phase 6 state:

- Status: listed → sold
- Order information recorded
- Profit metrics calculated

---

## Error Handling

### Order Polling Errors
- API rate limit → retry with backoff
- Partial data retrieval → log and retry next cycle
- Network error → use exponential backoff

### Data Reconciliation
- Order not found in database → investigate
- Duplicate orders → deduplicate on order_id
- Missing tracking → flag for manual review

---

## Scheduling

### Polling Frequency
- **Orders:** Every 4 hours (or configurable)
- **Returns:** Every 24 hours
- **Reports:** Daily at midnight UTC

### Backoff Strategy
- Exponential backoff on API errors
- Max retries: 5
- Initial backoff: 1 minute

---

## Next Phases

### Phase 8: Seller Analytics & Metrics
- Dashboard for seller metrics
- Profit by category / brand / time
- Best/worst performers
- Seasonal trends

### Phase 9: Automated Repricing & Monitoring
- Dynamic pricing based on demand
- Auto-adjust prices in response to competitors
- Stock monitoring
- Alert for low/slow items

### Phase 10: Multi-Channel Integration
- Amazon FBA integration
- Other marketplace support
- Centralized inventory

---

## Summary

Phase 7 closes the feedback loop: after items are listed (Phase 6), Phase 7 monitors sales, updates inventory, and generates insights. This enables Phase 8+ (analytics and repricing) to optimize seller performance.
