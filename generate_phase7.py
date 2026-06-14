#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 7: Inventory Sync & Order Management Design
"""

import json
from datetime import datetime
from pathlib import Path

def create_phase7_design_doc():
    content = r'''# Phase 7: Inventory Sync & Order Management

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
'''
    return content

def create_order_management_doc():
    content = r'''# Phase 7: Order Management Specification

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
'''
    return content

def create_phase7_completion_report(project_dir):
    report = {
        "project_name": "MarginScout",
        "phase": "Phase 7: Inventory Sync & Order Management Design",
        "status": "DESIGN_COMPLETE",
        "timestamp": datetime.now().isoformat(),
        "documents_created": [
            "docs/PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md",
            "docs/ORDER_MANAGEMENT_SPECIFICATION.md",
        ],
        "design_scope": {
            "order_polling": "eBay Orders API polling (4-hour frequency)",
            "inventory_tracking": "Update candidate status from 'listed' to 'sold'",
            "returns_management": "Handle return requests and update inventory",
            "sales_reporting": "Daily/weekly/monthly sales and profit metrics",
            "database_schema": "New orders and sales_report tables, candidates updates",
        },
        "key_components": [
            "OrderPoller (scheduled task)",
            "OrderParser (parse API responses)",
            "InventoryUpdater (update candidate status)",
            "ReturnsManager (handle return requests)",
            "SalesReporter (generate reports)",
        ],
        "data_models": {
            "OrderRecord": ["order_id", "listing_id", "sku", "buyer_username", "order_status", "purchase_price", "quantity", "purchase_date", "shipping_address", "tracking_number"],
            "InventoryStatus": ["sku", "candidate_id", "status", "listing_id", "order_id", "sold_price", "sold_date", "profit_margin", "net_income"],
        },
        "integration_dependencies": [
            "Phase 6 output (listing_id, sku, candidate_id)",
            "eBay Orders API credentials (from Phase 6 OAuth)",
            "Internal database (for inventory updates)",
        ],
        "future_phases": {
            "Phase 8": "Seller Analytics & Metrics (dashboard, trends, insights)",
            "Phase 9": "Automated Repricing & Monitoring (dynamic pricing, alerts)",
            "Phase 10": "Multi-Channel Integration (Amazon, other marketplaces)",
        },
        "next_steps": [
            "1. Review Phase 7 design with stakeholders",
            "2. Finalize database schema",
            "3. Begin Phase 7 implementation (order poller module)",
            "4. Implement Phase 6 tests (OAuth, API, integration)",
            "5. Plan Phase 8 (analytics)",
        ],
    }
    
    report_path = Path(project_dir) / "PHASE7_DESIGN_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report_path

def update_readme(project_dir):
    readme_path = Path(project_dir) / "README.md"
    
    phase7_section = r'''
---

## 📋 Phase 7: Inventory Sync & Order Management (Design)

**Status:** ✅ Design Complete  
**Date:** 2026-06-13

### Design Overview

Phase 7 implements real-time inventory synchronization with eBay and order management:

- **Order Polling:** Query eBay Orders API every 4 hours
- **Inventory Update:** Mark candidates as 'sold' with order details
- **Returns Management:** Handle return requests
- **Sales Reporting:** Daily/weekly/monthly metrics

### Key Components (Design)

- **OrderPoller** – Scheduled task to query eBay Orders API
- **OrderParser** – Parse and normalize eBay order responses
- **InventoryUpdater** – Update candidate status and link to orders
- **ReturnsManager** – Monitor and process return requests
- **SalesReporter** – Generate revenue and profit reports

### Database Schema (Proposed)

**New Tables:**
- `orders` – eBay order records
- `sales_report` – Daily aggregated metrics

**Updated Tables:**
- `candidates` – Add status, listing_id, order_id, sold_price, profit_margin, etc.

### Integration Flow

```
Phase 6 Output (live listings)
  ↓
Phase 7: Order Polling (scheduled)
  ↓
[eBay Orders API]
  ↓
[Parse Orders]
  ↓
[Update Inventory: listed → sold]
  ↓
[Record Order & Profit Metrics]
  ↓
Sales Report (Phase 8 input)
```

### Next Steps

- Phase 6: Implement unit tests & Sandbox integration
- Phase 7: Implement order polling and inventory update modules
- Phase 8: Analytics & metrics dashboard

---

## Project Status Summary

| Phase | Content | Status |
|-------|---------|--------|
| 2-5 | Research → Payload → Executor | ✅ Complete |
| 6 | OAuth & Live API (Sandbox) | ✅ Complete |
| 7 | Order Sync & Inventory Mgmt | ✅ Design |
| 8+ | Analytics, Repricing, Multi-channel | 📋 Roadmap |
'''
    
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "Phase 7:" not in content:
            with open(readme_path, "a", encoding="utf-8") as f:
                f.write(phase7_section)

def main():
    project_dir = Path.cwd()
    
    print("="*70)
    print("MarginScout Phase 7: Inventory Sync & Order Management Design")
    print("="*70)
    
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    print("\nCreating Phase 7 design documents...")
    
    print("✓ docs/PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md")
    with open(docs_dir / "PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md", "w", encoding="utf-8") as f:
        f.write(create_phase7_design_doc())
    
    print("✓ docs/ORDER_MANAGEMENT_SPECIFICATION.md")
    with open(docs_dir / "ORDER_MANAGEMENT_SPECIFICATION.md", "w", encoding="utf-8") as f:
        f.write(create_order_management_doc())
    
    print("\nCreating Phase 7 design report...")
    create_phase7_completion_report(project_dir)
    print("✓ PHASE7_DESIGN_REPORT.json")
    
    print("\nUpdating README.md...")
    update_readme(project_dir)
    print("✓ README.md updated")
    
    print("\n" + "="*70)
    print("Phase 7 Design: COMPLETE")
    print("="*70)
    print("\nGenerated files:")
    print("  - docs/PHASE7_INVENTORY_SYNC_AND_ORDER_MANAGEMENT.md")
    print("  - docs/ORDER_MANAGEMENT_SPECIFICATION.md")
    print("  - PHASE7_DESIGN_REPORT.json")
    print("  - README.md (updated)")
    print("\nNext: Phase 6 tests or Phase 7 implementation")

if __name__ == "__main__":
    main()
