#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 5: eBay Executor & Dry-Run Implementation Design
Generates design docs, data models, examples, and skeleton code.
"""

import os
import json
from datetime import datetime
from pathlib import Path

# ============================================================================
# PHASE 5 DESIGN: eBay Executor & Dry-Run
# ============================================================================

def create_phase5_design_doc():
    """Create docs/PHASE5_EBAY_EXECUTOR.md"""
    content = r'''# Phase 5: eBay Executor & Dry-Run Implementation Design

**Date:** 2026-06-13  
**Status:** Design Phase  
**Target:** eBay listing execution preparation, price strategy, category resolution, dry-run validation

## Overview

Phase 5 transforms validated eBay Payload Records into execution-ready listings. The Executor module applies price strategies, resolves eBay categories, performs final readiness checks, and executes a **dry-run** (no live API call) to validate the payload before handoff to Phase 6 (live eBay API integration).

### Key Responsibilities

1. **Price Strategy Application** – Reference price + margin policy + platform fees → final eBay price
2. **Category Resolution** – Internal normalized category → eBay Category ID (leaf-node detection)
3. **Readiness Judgment** – Final validation before execution (all mandatory fields, price calculated, category resolved, images available)
4. **Dry-Run Execution** – Simulate listing creation without API call; generate mock response; capture validation results
5. **Execution Audit** – Record timestamp, candidate_id, SKU, payload version, pricing decision, category resolution, dry-run result
6. **Error Handling** – Categorize errors (recoverable, manual-review, reject); retry logic; fallback options

---

## Overall Executor Flow

```
ListingReadyRecord
       ↓
[Price Strategy Application]
       ↓
[Category Resolution]
       ↓
[Pre-Execution Validation]
       ↓
[Readiness Judgment]
       ↓
[Dry-Run Execution]
       ↓
[Execution Audit Log]
       ↓
ExecutionReadyPayload + AuditTrail + MockResponse
```

### Step Details

**1. Price Strategy Application**
- Input: Reference price (from research), margin policy, platform fees (eBay FVF ~12.9%)
- Process: Calculate final eBay price = (Reference Price) / (1 - Margin % - Platform FVF)
- Output: Calculated price, pricing decision log
- Policy: Price must be ≥ min_price, ≤ max_price; round to nearest $0.01

**2. Category Resolution**
- Input: Internal normalized category (e.g., "Electronics > Cameras > Lenses")
- Process: Map to eBay Category Tree; identify leaf-node category ID
- Output: eBay Category ID, category path, leaf-node flag
- Policy: Single category per listing; leaf-node required; fallback to "Miscellaneous" if unresolved

**3. Pre-Execution Validation**
- Checks: Title length, description length, price range, quantity, condition enum, category validity, image count
- Errors: Hard errors (missing mandatory), soft warnings (minor issues), pending review (needs user confirmation)
- Output: Validation report with error list and recommendations

**4. Readiness Judgment**
- Criteria:
  - All mandatory fields present (title, price, category, condition, sku)
  - Price calculated and within valid range
  - Category resolved to eBay ID
  - Images available (at least 1; path exists in data/images/{SKU}/)
  - No hard errors in validation
  - Candidate_id and audit trail populated
- Output: Readiness level (ready / pending_review / incomplete / rejected)

**5. Dry-Run Execution**
- Input: Execution-ready payload
- Process: Simulate listing creation; generate mock eBay response (listing_id, status, warnings)
- Output: Mock response (no API call), execution validation results
- Policy: Dry-run is deterministic; same payload → same mock response

**6. Execution Audit Log**
- Records: Timestamp, candidate_id, SKU, payload version, reference_price, calculated_price, margin_policy, category_id, category_path, validation_status, dry_run_result, next_action
- Purpose: Traceability, audit trail, retry/recovery decisions

---

## Input Specification

**Required from Phase 4 (ListingReadyRecord):**
- title (string, ≤ 80 chars)
- description (string, ≤ 4000 chars)
- sku (string, format MARGIN-YYYYMMDD-NNNN)
- category (string, internal normalized form)
- condition (enum: new / like_new / good / fair / for_parts_or_not_working)
- price (float, pre-calculated or placeholder)
- quantity (int, ≥ 1)
- images (list of file paths)
- candidate_id (string, for audit)
- source_url (string, for audit)
- user_notes (string, optional, for audit)

**Optional inputs:**
- reference_price (float, for price strategy)
- margin_policy (float, % margin expectation, default 15%)
- platform_fees (float, eBay FVF %, default 12.9%)
- listing_duration (int, days, default 30)

---

## Internal Data Model Layers

### Layer 1: Price Preparation (PricePreparationRecord)
```json
{
  "reference_price": 100.0,
  "margin_policy_percent": 15.0,
  "platform_fee_percent": 12.9,
  "calculated_price": 110.45,
  "price_calculation_log": {
    "formula": "(reference_price) / (1 - margin% - fee%)",
    "step1_divisor": 0.7210,
    "step2_calculated": 110.4577,
    "step3_rounded": 110.45
  },
  "price_valid": true,
  "price_status": "ready"
}
```

### Layer 2: Category Preparation (CategoryPreparationRecord)
```json
{
  "internal_category": "Electronics > Cameras > Lenses",
  "ebay_category_id": 625,
  "ebay_category_path": "Electronics > Cameras & Photo > Lenses & Filters > Lenses",
  "is_leaf_node": true,
  "category_resolution_log": {
    "mapping_source": "eBay Category Tree 2026-06",
    "confidence": 0.95,
    "fallback_used": false
  },
  "category_valid": true,
  "category_status": "resolved"
}
```

### Layer 3: Validated Payload (ValidatedExecutionPayload)
```json
{
  "sku": "MARGIN-20260613-0001",
  "title": "Canon EF 70-200mm f/2.8 IS II USM Lens",
  "description": "Professional telephoto lens...",
  "price": 110.45,
  "quantity": 1,
  "condition": "new",
  "category_id": 625,
  "images": ["data/images/MARGIN-20260613-0001/img1.jpg"],
  "candidate_id": "cand_20260613_001",
  "validation_report": {
    "hard_errors": [],
    "soft_warnings": [],
    "readiness_level": "ready"
  },
  "audit": {
    "price_data": { },
    "category_data": { },
    "validation_timestamp": "2026-06-13T14:35:22Z"
  }
}
```

### Layer 4: Final eBay Payload (FinalEBayPayload)
```json
{
  "listing": {
    "title": "Canon EF 70-200mm f/2.8 IS II USM Lens",
    "description": "Professional telephoto lens...",
    "price": 110.45,
    "quantity": 1,
    "condition": "new",
    "category_id": 625,
    "item_specifics": {
      "brand": "Canon",
      "model": "EF 70-200mm f/2.8 IS II USM",
      "type": "Telephoto Lens"
    },
    "pictures": [
      { "picture_url": "data/images/MARGIN-20260613-0001/img1.jpg" }
    ]
  },
  "metadata": {
    "sku": "MARGIN-20260613-0001",
    "candidate_id": "cand_20260613_001",
    "source_url": "https://example.com/item/12345",
    "user_notes": "Great condition, minor box wear",
    "created_at": "2026-06-13T14:35:22Z",
    "version": "1.0"
  }
}
```

---

## Design Decisions

### Title Policy
- Max 80 characters
- Format: "[Brand] [Model/Type] [Key Feature]"
- Do not truncate; reject if exceeds limit
- Special characters: escape HTML entities

### Description Policy
- Max 4000 characters
- Format: HTML-escaped text (no raw tags)
- Include: condition, brand, model, features, notes
- Template-based generation from listing_record fields

### Condition Mapping
- Internal enum → eBay enum (1-5):
  - new → 3000 (New)
  - like_new → 3000 (New)
  - good → 3000 (New)
  - fair → 7000 (Used)
  - for_parts_or_not_working → 7000 (Used)

### Price Policy
- Calculation: (reference_price) / (1 - margin% - platform_fee%)
- Validation: price ≥ $0.99, ≤ $999,999.99
- Rounding: nearest $0.01
- Storage: 2 decimal places

### Quantity Policy
- Fixed: 1 item per listing (future: multi-item support in Phase 6+)
- Validation: quantity ≥ 1

### Category Policy
- Single category per listing (eBay requirement)
- Must be leaf-node in eBay category tree
- Fallback: "Miscellaneous" (ID 15687) if unresolved
- Mapping: internal category → eBay Category ID (lookup table or API)

### Image Policy
- Minimum: 1 image
- Maximum: 12 images
- Storage: SKU-based directory (data/images/{SKU}/)
- Format: JPEG, PNG (validated at Phase 3)
- Missing: Error if no images found in directory

### Readiness Levels
- **ready** – all checks pass, dry-run successful, ready for Phase 6
- **pending_review** – soft warnings present, manual review recommended
- **incomplete** – hard errors or missing mandatory fields
- **rejected** – critical errors; cannot proceed to Phase 6

---

## Dry-Run Execution Design

**Purpose:** Validate payload structure and business logic without calling live eBay API.

**Inputs:**
- Validated execution payload (Layer 3)
- Mock eBay category tree (static lookup)
- Mock fee calculator (deterministic)

**Process:**
1. Check payload completeness
2. Simulate eBay validation rules
3. Generate mock listing_id (deterministic: hash of SKU + timestamp)
4. Assign mock status ("draft" or "ready_for_activation")
5. Collect validation warnings (if any)
6. Return mock response

**Outputs:**
```json
{
  "mock_response": {
    "listing_id": "mock_20260613_abc123def456",
    "sku": "MARGIN-20260613-0001",
    "status": "draft",
    "fee_estimate": {
      "insertion_fee": 0.00,
      "final_value_fee": 14.25,
      "total_fee": 14.25
    },
    "warnings": []
  },
  "execution_valid": true,
  "execution_timestamp": "2026-06-13T14:35:22Z",
  "next_action": "ready_for_phase_6"
}
```

### Error Handling Strategy

**Error Categories**
*Hard Errors (block execution)*
- Missing title, price, category, condition, SKU
- Price out of range
- Category unresolved
- No images found
- Validation score < 70%

*Soft Warnings (allow with confirmation)*
- Title near length limit
- Description minor issues
- Low-confidence category mapping
- Missing optional fields (notes, tags)

*Manual Review (require user decision)*
- Category mapping confidence < 80%
- Unusual price (> 5x reference_price)
- Duplicate SKU detected

*Skip / Retry (defer or retry)*
- Transient category lookup failure
- Temporary price calculation issue
- Recoverable file I/O error

**Retry Logic**
- Max retries: 3
- Backoff: exponential (1s, 2s, 4s)
- Trigger: transient errors only

### Execution Audit Log
**Fields logged:**
- timestamp (ISO 8601)
- candidate_id (string)
- sku (string)
- payload_version (string)
- reference_price (float)
- calculated_price (float)
- margin_policy (float)
- platform_fees (float)
- ebay_category_id (int)
- ebay_category_path (string)
- validation_status (string: hard_error / soft_warning / ready / pending_review)
- dry_run_result (string: success / partial / failed)
- mock_listing_id (string)
- warnings (list of strings)
- user_notes (string, for audit)
- next_action (string: proceed_to_phase_6 / manual_review / retry / reject)

**Example:**
```json
{
  "timestamp": "2026-06-13T14:35:22Z",
  "candidate_id": "cand_20260613_001",
  "sku": "MARGIN-20260613-0001",
  "payload_version": "1.0",
  "reference_price": 100.0,
  "calculated_price": 110.45,
  "margin_policy_percent": 15.0,
  "platform_fees_percent": 12.9,
  "ebay_category_id": 625,
  "ebay_category_path": "Electronics > Cameras & Photo > Lenses & Filters > Lenses",
  "validation_status": "ready",
  "dry_run_result": "success",
  "mock_listing_id": "mock_20260613_abc123def456",
  "warnings": [],
  "user_notes": "No issues detected.",
  "next_action": "proceed_to_phase_6"
}
```

### Handoff to Phase 6
**Phase 6 Input:**
- Execution audit log (JSON)
- Final eBay payload (Layer 4)
- Mock response (for reference)
- Readiness level (ready / pending_review / incomplete / rejected)

**Phase 6 Responsibility:**
- Authenticate with live eBay API
- Submit final payload to eBay
- Handle eBay API responses (errors, rate limits, etc.)
- Update candidate status to "listed"
- Return real listing_id and activation link

**Preconditions for Phase 6:**
- Readiness level = "ready"
- No hard errors
- Dry-run successful

## Summary
Phase 5 is a validation and preparation layer that applies business logic (price strategy, category resolution) and simulates execution (dry-run) before handing off to Phase 6 (live API). The Executor ensures that all listings are well-formed, priced correctly, categorized appropriately, and ready for eBay API submission.

**Next Phase:** Phase 6 – eBay API Integration & Live Listing
'''
    return content

def create_price_strategy_doc():
    """Create docs/EBAY_PRICE_STRATEGY.md"""
    content = r'''# eBay Price Strategy Model

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
'''
    return content

def create_category_mapping_doc():
    """Create docs/EBAY_CATEGORY_MAPPING.md"""
    content = r'''# eBay Category Mapping Specification

Date: 2026-06-13

## Overview
The category resolver maps internal normalized categories to eBay Category IDs for use in live listings. This ensures that all listings are placed in valid, leaf-node categories within eBay's category tree.

## Mapping Strategy
**Internal Category Format**
```
"Electronics > Cameras > Lenses"
"Electronics > Photography Equipment > Accessories"
"Collectibles > Trading Cards > Pokemon"
```

**eBay Category ID Format**
```
eBay Category ID: 625 (Lenses & Filters)
eBay Category Path: Electronics > Cameras & Photo > Lenses & Filters > Lenses
Leaf-Node: Yes
```

**Mapping Lookup Table (Sample)**
| Internal Category | eBay Cat ID | eBay Path | Leaf | Confidence |
| --- | --- | --- | --- | --- |
| Electronics > Cameras > Lenses | 625 | Electronics > Cameras & Photo > ... > Lenses | Yes | 0.95 |
| Electronics > Cameras > Filters | 29742 | Electronics > Cameras & Photo > ... > Filters | Yes | 0.90 |
| Collectibles > Trading Cards > Pokemon | 39439 | Collectibles > Trading Cards > ... | Yes | 0.88 |

## Resolution Process
1. Exact Match: Search internal category in lookup table
2. Partial Match: Find closest match in hierarchy
3. Confidence Check: If confidence < 0.80, flag for manual review
4. Fallback: Use "Miscellaneous" (ID 15687) if no match found

## Fallback Category
- ID: 15687
- Name: "Miscellaneous"
- Usage: For items that don't fit standard categories
- Limitation: May result in lower visibility

## Leaf-Node Requirement
- eBay requires listings to be in leaf-node categories only
- A leaf-node is the deepest level in the eBay category tree
- Example leaf-node: "Electronics > Cameras & Photo > Lenses & Filters > Lenses"
- Example non-leaf: "Electronics > Cameras & Photo" (has children, invalid for listing)

## Implementation Notes
- Mapping table should be updated quarterly
- Implement caching to reduce lookup latency
- Log all mappings with confidence scores for audit
- Support manual override via user review
'''
    return content

def create_price_strategy_sample():
    """Create examples/price_strategy_sample.json"""
    sample = {
        "pricing_scenarios": [
            {
                "scenario_id": "ps_001",
                "item_name": "Canon EF 70-200mm f/2.8 IS II USM Lens",
                "reference_price": 100.00,
                "margin_policy_percent": 15.0,
                "platform_fee_percent": 12.9,
                "calculation": {
                    "formula": "(reference_price) / (1 - margin% - fee%)",
                    "step1_divisor_calc": "1 - 0.15 - 0.129",
                    "step1_divisor": 0.721,
                    "step2_calculated": 138.6853,
                    "step3_rounded_ceiling": 138.69,
                    "final_price": 138.69
                },
                "validation": {
                    "in_min_bound": True,
                    "in_max_bound": True,
                    "price_valid": True
                },
                "notes": "Standard pricing scenario"
            },
            {
                "scenario_id": "ps_002",
                "item_name": "Nike Air Max 270 Sneakers",
                "reference_price": 80.00,
                "margin_policy_percent": 20.0,
                "platform_fee_percent": 12.9,
                "calculation": {
                    "formula": "(reference_price) / (1 - margin% - fee%)",
                    "step1_divisor_calc": "1 - 0.20 - 0.129",
                    "step1_divisor": 0.671,
                    "step2_calculated": 119.2252,
                    "step3_rounded_ceiling": 119.23,
                    "final_price": 119.23
                },
                "validation": {
                    "in_min_bound": True,
                    "in_max_bound": True,
                    "price_valid": True
                },
                "notes": "Higher margin for popular consumer item"
            },
            {
                "scenario_id": "ps_003",
                "item_name": "Sony WH-1000XM5 Headphones",
                "reference_price": 350.00,
                "margin_policy_percent": 12.0,
                "platform_fee_percent": 12.9,
                "calculation": {
                    "formula": "(reference_price) / (1 - margin% - fee%)",
                    "step1_divisor_calc": "1 - 0.12 - 0.129",
                    "step1_divisor": 0.751,
                    "step2_calculated": 465.9120,
                    "step3_rounded_ceiling": 465.92,
                    "final_price": 465.92
                },
                "validation": {
                    "in_min_bound": True,
                    "in_max_bound": True,
                    "price_valid": True
                },
                "notes": "Lower margin for high-volume items"
            }
        ],
        "fee_estimates": [
            {
                "sku": "MARGIN-20260613-0001",
                "item_price": 138.69,
                "insertion_fee": 0.00,
                "final_value_fee_percent": 12.9,
                "final_value_fee": 17.89,
                "total_fee": 17.89,
                "net_income": 120.80
            },
            {
                "sku": "MARGIN-20260613-0002",
                "item_price": 119.23,
                "insertion_fee": 0.00,
                "final_value_fee_percent": 12.9,
                "final_value_fee": 15.38,
                "total_fee": 15.38,
                "net_income": 103.85
            }
        ]
    }
    return json.dumps(sample, indent=2, ensure_ascii=False)

def create_dry_run_sample():
    """Create examples/ebay_dry_run_sample.json"""
    sample = {
        "dry_run_executions": [
            {
                "execution_id": "exec_20260613_001",
                "timestamp": "2026-06-13T14:35:22Z",
                "sku": "MARGIN-20260613-0001",
                "candidate_id": "cand_20260613_001",
                "payload_version": "1.0",
                "item_title": "Canon EF 70-200mm f/2.8 IS II USM Lens",
                "mock_response": {
                    "status": "success",
                    "mock_listing_id": "mock_20260613_abc123def456",
                    "mock_item_id": "386547829380",
                    "status_code": "draft",
                    "activation_link": "https://ebay.com/itm/mock_386547829380",
                    "fee_estimate": {
                        "insertion_fee": 0.00,
                        "final_value_fee": 17.89,
                        "total_fee": 17.89
                    }
                },
                "validation_results": {
                    "title_valid": True,
                    "description_valid": True,
                    "price_valid": True,
                    "category_valid": True,
                    "condition_valid": True,
                    "images_valid": True,
                    "overall_score": 0.98
                },
                "warnings": [],
                "next_action": "ready_for_phase_6"
            },
            {
                "execution_id": "exec_20260613_002",
                "timestamp": "2026-06-13T14:36:15Z",
                "sku": "MARGIN-20260613-0002",
                "candidate_id": "cand_20260613_002",
                "payload_version": "1.0",
                "item_title": "Nike Air Max 270 Sneakers",
                "mock_response": {
                    "status": "success",
                    "mock_listing_id": "mock_20260613_def789ghi012",
                    "mock_item_id": "386547829381",
                    "status_code": "draft",
                    "activation_link": "https://ebay.com/itm/mock_386547829381",
                    "fee_estimate": {
                        "insertion_fee": 0.00,
                        "final_value_fee": 15.38,
                        "total_fee": 15.38
                    }
                },
                "validation_results": {
                    "title_valid": True,
                    "description_valid": True,
                    "price_valid": True,
                    "category_valid": True,
                    "condition_valid": True,
                    "images_valid": False,
                    "overall_score": 0.85
                },
                "warnings": [
                    "Only 1 image provided; recommend 2+ for better visibility"
                ],
                "next_action": "pending_review"
            }
        ]
    }
    return json.dumps(sample, indent=2, ensure_ascii=False)

def create_execution_audit_log_sample():
    """Create examples/execution_audit_log_sample.json"""
    sample = {
        "audit_logs": [
            {
                "log_id": "audit_20260613_001",
                "timestamp": "2026-06-13T14:35:22Z",
                "candidate_id": "cand_20260613_001",
                "sku": "MARGIN-20260613-0001",
                "payload_version": "1.0",
                "reference_price": 100.00,
                "calculated_price": 138.69,
                "margin_policy_percent": 15.0,
                "platform_fees_percent": 12.9,
                "ebay_category_id": 625,
                "ebay_category_path": "Electronics > Cameras & Photo > Lenses & Filters > Lenses",
                "validation_status": "ready",
                "dry_run_result": "success",
                "mock_listing_id": "mock_20260613_abc123def456",
                "warnings": [],
                "user_notes": "Canon lens in excellent condition. Verified price calculation.",
                "next_action": "proceed_to_phase_6"
            },
            {
                "log_id": "audit_20260613_002",
                "timestamp": "2026-06-13T14:36:15Z",
                "candidate_id": "cand_20260613_002",
                "sku": "MARGIN-20260613-0002",
                "payload_version": "1.0",
                "reference_price": 80.00,
                "calculated_price": 119.23,
                "margin_policy_percent": 20.0,
                "platform_fees_percent": 12.9,
                "ebay_category_id": 15687,
                "ebay_category_path": "Miscellaneous",
                "validation_status": "pending_review",
                "dry_run_result": "partial",
                "mock_listing_id": "mock_20260613_def789ghi012",
                "warnings": [
                    "Category confidence < 0.80; using fallback (Miscellaneous)",
                    "Only 1 image provided"
                ],
                "user_notes": "Nike sneakers. Category resolution needs user confirmation.",
                "next_action": "manual_review"
            },
            {
                "log_id": "audit_20260613_003",
                "timestamp": "2026-06-13T14:37:00Z",
                "candidate_id": "cand_20260613_003",
                "sku": "MARGIN-20260613-0003",
                "payload_version": "1.0",
                "reference_price": 350.00,
                "calculated_price": 465.92,
                "margin_policy_percent": 12.0,
                "platform_fees_percent": 12.9,
                "ebay_category_id": None,
                "ebay_category_path": None,
                "validation_status": "incomplete",
                "dry_run_result": "failed",
                "mock_listing_id": None,
                "warnings": [
                    "Hard error: Category unresolved",
                    "Hard error: No images found in data/images/MARGIN-20260613-0003/"
                ],
                "user_notes": "Sony headphones. Missing images and category mapping failure.",
                "next_action": "reject"
            }
        ]
    }
    return json.dumps(sample, indent=2, ensure_ascii=False)

def create_mapping_reference():
    """Create examples/listing_to_payload_mapping.md"""
    content = r'''# Listing to Payload Mapping Reference

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
'''
    return content

def create_skeleton_code(project_dir):
    """Create src/executor/ skeleton code"""
    executor_dir = Path(project_dir) / "src" / "executor"
    executor_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py
    init_content = r'''"""
MarginScout Phase 5: eBay Executor & Dry-Run Module
Transforms listing-ready records into execution-ready payloads.
Applies price strategy, resolves categories, and executes dry-run.
"""

from .price_calculator import PriceCalculator
from .category_resolver import CategoryResolver
from .ebay_api_client import EBayAPIClient
from .executor import Executor
from .dry_run_executor import DryRunExecutor

__all__ = [
    "PriceCalculator",
    "CategoryResolver",
    "EBayAPIClient",
    "Executor",
    "DryRunExecutor",
]
'''
    with open(executor_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write(init_content)

    # price_calculator.py
    price_calc_content = r'''"""
Price Calculator Module
Applies margin policy and platform fees to reference price.
Formula: price = reference_price / (1 - margin% - fee%)
"""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class PriceCalculationResult:
    """Result of price calculation."""
    reference_price: float
    margin_policy_percent: float
    platform_fee_percent: float
    calculated_price: float
    calculation_log: Dict
    price_valid: bool
    price_status: str

class PriceCalculator:
    """Calculate eBay listing price from reference price."""

    def __init__(self, margin_percent: float = 15.0, platform_fee_percent: float = 12.9):
        """
        Initialize price calculator.
        
        Args:
            margin_percent: Desired margin percentage (default 15%)
            platform_fee_percent: eBay FVF percentage (default 12.9%)
        """
        self.margin_percent = margin_percent
        self.platform_fee_percent = platform_fee_percent

    def calculate_price(self, reference_price: float) -> PriceCalculationResult:
        """
        Calculate eBay price from reference price.
        
        Formula: price = reference_price / (1 - margin% - fee%)
        """
        raise NotImplementedError("Price calculation not yet implemented")

    def get_fee_estimate(self, final_price: float) -> Dict:
        """
        Get fee estimate for final price.
        """
        raise NotImplementedError("Fee estimation not yet implemented")
'''
    with open(executor_dir / "price_calculator.py", "w", encoding="utf-8") as f:
        f.write(price_calc_content)

    # category_resolver.py
    category_resolver_content = r'''"""
Category Resolver Module
Maps internal normalized categories to eBay Category IDs.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

@dataclass
class CategoryResolutionResult:
    """Result of category resolution."""
    internal_category: str
    ebay_category_id: Optional[int]
    ebay_category_path: Optional[str]
    is_leaf_node: bool
    confidence: float
    resolution_log: Dict
    category_valid: bool
    category_status: str

class CategoryResolver:
    """Resolve internal categories to eBay Category IDs."""

    # TODO: Load eBay Category Tree mapping from external source or config
    # For now, use static lookup table
    CATEGORY_MAPPING = {
        "Electronics > Cameras > Lenses": {
            "ebay_category_id": 625,
            "ebay_category_path": "Electronics > Cameras & Photo > Lenses & Filters > Lenses",
            "is_leaf_node": True,
            "confidence": 0.95,
        },
        # Add more mappings as needed
    }

    FALLBACK_CATEGORY = {
        "ebay_category_id": 15687,
        "ebay_category_path": "Miscellaneous",
        "is_leaf_node": True,
        "confidence": 0.0,
    }

    def resolve_category(self, internal_category: str) -> CategoryResolutionResult:
        """
        Resolve internal category to eBay Category ID.
        """
        raise NotImplementedError("Category resolution not yet implemented")
'''
    with open(executor_dir / "category_resolver.py", "w", encoding="utf-8") as f:
        f.write(category_resolver_content)

    # ebay_api_client.py
    ebay_api_client_content = r'''"""
eBay API Client Module (Skeleton)
Placeholder for future eBay API authentication and endpoint calls.
Phase 5 does not execute live API calls; Phase 6 will implement this.
"""

from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class EBayAPIResponse:
    """Response from eBay API."""
    status_code: int
    data: Dict
    errors: list
    timestamp: str

class EBayAPIClient:
    """eBay API client for authentication and listing creation."""

    def __init__(self, app_id: Optional[str] = None, auth_token: Optional[str] = None):
        """
        Initialize eBay API client.
        """
        self.app_id = app_id
        self.auth_token = auth_token
        self.base_url = "https://api.ebay.com"  # Production endpoint

    def authenticate(self) -> bool:
        """
        Authenticate with eBay API.
        """
        raise NotImplementedError("eBay authentication not yet implemented (Phase 6)")

    def create_listing(self, payload: Dict) -> EBayAPIResponse:
        """
        Create listing on eBay.
        """
        raise NotImplementedError("Live API call not yet implemented (Phase 6)")
'''
    with open(executor_dir / "ebay_api_client.py", "w", encoding="utf-8") as f:
        f.write(ebay_api_client_content)

    # executor.py
    executor_content = r'''"""
Main Executor Module
Orchestrates price strategy, category resolution, validation, and handoff.
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime

@dataclass
class ExecutionAuditLog:
    """Audit log entry for execution."""
    timestamp: str
    candidate_id: str
    sku: str
    payload_version: str
    reference_price: float
    calculated_price: float
    margin_policy_percent: float
    platform_fees_percent: float
    ebay_category_id: Optional[int]
    ebay_category_path: Optional[str]
    validation_status: str
    dry_run_result: str
    mock_listing_id: Optional[str]
    warnings: List[str]
    user_notes: Optional[str]
    next_action: str

class Executor:
    """Main executor for payload preparation and readiness judgment."""

    def __init__(self, price_calculator, category_resolver, dry_run_executor):
        """
        Initialize executor.
        """
        self.price_calculator = price_calculator
        self.category_resolver = category_resolver
        self.dry_run_executor = dry_run_executor

    def execute(self, listing_ready_record: Dict) -> Dict:
        """
        Execute full payload preparation workflow.
        """
        raise NotImplementedError("Executor not yet implemented")

    def judge_readiness(self, validation_report: Dict) -> str:
        """
        Judge readiness level based on validation.
        """
        raise NotImplementedError("Readiness judgment not yet implemented")
'''
    with open(executor_dir / "executor.py", "w", encoding="utf-8") as f:
        f.write(executor_content)

    # dry_run_executor.py
    dry_run_executor_content = r'''"""
Dry-Run Executor Module
Simulates listing creation without calling live eBay API.
"""

from dataclasses import dataclass
from typing import Dict, Optional
from datetime import datetime
import hashlib

@dataclass
class DryRunResponse:
    """Mock response from dry-run execution."""
    status: str  # "success" or "failed"
    mock_listing_id: Optional[str]
    mock_item_id: Optional[str]
    status_code: str  # "draft" or error
    activation_link: Optional[str]
    fee_estimate: Dict
    warnings: list
    execution_valid: bool
    next_action: str

class DryRunExecutor:
    """Executor for dry-run simulations."""

    def execute_dry_run(self, execution_payload: Dict) -> DryRunResponse:
        """
        Execute dry-run simulation of listing creation.
        """
        raise NotImplementedError("Dry-run execution not yet implemented")

    def _generate_mock_listing_id(self, sku: str, timestamp: str) -> str:
        """
        Generate deterministic mock listing_id.
        """
        raise NotImplementedError("Mock ID generation not yet implemented")
'''
    with open(executor_dir / "dry_run_executor.py", "w", encoding="utf-8") as f:
        f.write(dry_run_executor_content)


def create_phase5_completion_report(project_dir):
    """Create PHASE5_COMPLETION_REPORT.json"""
    report = {
        "project_name": "MarginScout",
        "phase": "Phase 5: eBay Executor & Dry-Run Implementation Design",
        "status": "COMPLETED",
        "timestamp": datetime.now().isoformat(),
        "documents_created": [
            "docs/PHASE5_EBAY_EXECUTOR.md",
            "docs/EBAY_PRICE_STRATEGY.md",
            "docs/EBAY_CATEGORY_MAPPING.md",
        ],
        "examples_created": [
            "examples/price_strategy_sample.json",
            "examples/ebay_dry_run_sample.json",
            "examples/execution_audit_log_sample.json",
            "examples/listing_to_payload_mapping.md",
        ],
        "skeleton_code_created": [
            "src/executor/__init__.py",
            "src/executor/price_calculator.py",
            "src/executor/category_resolver.py",
            "src/executor/ebay_api_client.py",
            "src/executor/executor.py",
            "src/executor/dry_run_executor.py",
        ],
        "key_findings": {
            "executor_responsibility": "Transform ListingReadyRecord into ExecutionReadyPayload by applying price strategy, resolving categories, validating, and executing dry-run",
            "price_formula": "price = reference_price / (1 - margin% - fee%)",
            "category_policy": "Single category, leaf-node required, fallback to Miscellaneous (ID 15687) if unresolved",
            "readiness_levels": ["ready", "pending_review", "incomplete", "rejected"],
            "dry_run_design": "Deterministic simulation without live API call; generates mock response for validation",
            "audit_policy": "Log candidate_id, sku, pricing, category resolution, validation results, dry-run outcome for traceability",
            "phase_6_handoff": "Execution-ready payload + audit trail + mock response → live eBay API integration"
        },
        "design_principles": [
            "Price strategy is deterministic and configurable",
            "Category resolution supports exact match, partial match, and fallback",
            "Dry-run is deterministic; same payload → same response",
            "Full audit trail retained for traceability",
            "Readiness judgment based on validation and business rules",
            "No live API calls in Phase 5; Phase 6 implements live integration"
        ],
        "next_phase": "Phase 6: eBay API Integration & Live Listing (implement authenticate(), create_listing(), handle API responses, update candidate status, return real listing_id)",
        "implementation_notes": [
            "Price calculator: implement margin + fee calculation with rounding",
            "Category resolver: implement mapping lookup with confidence scoring",
            "Dry-run executor: implement deterministic mock response generation",
            "Executor: orchestrate all components and generate audit log",
            "Phase 5 does not call live eBay API; Phase 6 will implement EBayAPIClient.create_listing()"
        ],
        "files_modified": [
            "README.md (Phase 5 status section added)"
        ]
    }
    
    report_path = Path(project_dir) / "PHASE5_COMPLETION_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    return report_path


def update_readme(project_dir):
    """Update README.md with Phase 5 status"""
    readme_path = Path(project_dir) / "README.md"
    
    phase5_section = """
---

## 📋 Phase 5: eBay Executor & Dry-Run Implementation Design
**Status**: ✅ Completed
**Date**: 2026-06-13

### Deliverables
- docs/PHASE5_EBAY_EXECUTOR.md – Overall executor design, workflow, readiness judgment, dry-run, audit
- docs/EBAY_PRICE_STRATEGY.md – Price calculation model (margin + fees)
- docs/EBAY_CATEGORY_MAPPING.md – Category resolution specification
- examples/price_strategy_sample.json – Sample price calculations
- examples/ebay_dry_run_sample.json – Sample dry-run outputs
- examples/execution_audit_log_sample.json – Sample audit trails
- examples/listing_to_payload_mapping.md – Field mapping reference
- src/executor/ – Skeleton code (price_calculator, category_resolver, executor, dry_run_executor)

### Key Design Decisions
- Price Formula: price = reference_price / (1 - margin% - fee%)
- Category Policy: Single category, leaf-node required, fallback to "Miscellaneous" if unresolved
- Readiness Levels: ready, pending_review, incomplete, rejected
- Dry-Run Design: Deterministic simulation without live API call
- Audit Trail: Full traceability with candidate_id, SKU, pricing, category, validation results

### Handoff to Phase 6
- Execution-ready payload (Layer 4)
- Audit trail (timestamp, pricing decision, category resolution, validation results)
- Mock response (for reference)
- Readiness level (ready / pending_review / incomplete / rejected)

Phase 6 Responsibility: Authenticate with live eBay API, submit payload, handle responses, update status.
"""
    
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if "Phase 5:" not in content:
            with open(readme_path, "a", encoding="utf-8") as f:
                f.write(phase5_section)
    else:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(phase5_section)


def main():
    """Generate all Phase 5 artifacts"""
    project_dir = Path.cwd()
    
    # Create docs
    print("Creating docs/PHASE5_EBAY_EXECUTOR.md...")
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    with open(docs_dir / "PHASE5_EBAY_EXECUTOR.md", "w", encoding="utf-8") as f:
        f.write(create_phase5_design_doc())
    print("✓ docs/PHASE5_EBAY_EXECUTOR.md")
    
    print("Creating docs/EBAY_PRICE_STRATEGY.md...")
    with open(docs_dir / "EBAY_PRICE_STRATEGY.md", "w", encoding="utf-8") as f:
        f.write(create_price_strategy_doc())
    print("✓ docs/EBAY_PRICE_STRATEGY.md")
    
    print("Creating docs/EBAY_CATEGORY_MAPPING.md...")
    with open(docs_dir / "EBAY_CATEGORY_MAPPING.md", "w", encoding="utf-8") as f:
        f.write(create_category_mapping_doc())
    print("✓ docs/EBAY_CATEGORY_MAPPING.md")
    
    # Create examples
    print("Creating examples/price_strategy_sample.json...")
    examples_dir = project_dir / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    with open(examples_dir / "price_strategy_sample.json", "w", encoding="utf-8") as f:
        f.write(create_price_strategy_sample())
    print("✓ examples/price_strategy_sample.json")
    
    print("Creating examples/ebay_dry_run_sample.json...")
    with open(examples_dir / "ebay_dry_run_sample.json", "w", encoding="utf-8") as f:
        f.write(create_dry_run_sample())
    print("✓ examples/ebay_dry_run_sample.json")
    
    print("Creating examples/execution_audit_log_sample.json...")
    with open(examples_dir / "execution_audit_log_sample.json", "w", encoding="utf-8") as f:
        f.write(create_execution_audit_log_sample())
    print("✓ examples/execution_audit_log_sample.json")
    
    # Using existing file listing_to_payload_mapping.md, but overwrite if required by user
    print("Creating examples/listing_to_payload_mapping.md...")
    with open(examples_dir / "listing_to_payload_mapping.md", "w", encoding="utf-8") as f:
        f.write(create_mapping_reference())
    print("✓ examples/listing_to_payload_mapping.md")
    
    # Create skeleton code
    print("Creating src/executor/ skeleton code...")
    create_skeleton_code(project_dir)
    print("✓ src/executor/__init__.py")
    print("✓ src/executor/price_calculator.py")
    print("✓ src/executor/category_resolver.py")
    print("✓ src/executor/ebay_api_client.py")
    print("✓ src/executor/executor.py")
    print("✓ src/executor/dry_run_executor.py")
    
    # Create completion report
    print("Creating PHASE5_COMPLETION_REPORT.json...")
    report_path = create_phase5_completion_report(project_dir)
    print(f"✓ {report_path}")
    
    # Update README
    print("Updating README.md...")
    update_readme(project_dir)
    print("✓ README.md")
    
    print("\n" + "="*70)
    print("Phase 5: eBay Executor & Dry-Run Implementation Design COMPLETED")
    print("="*70)
    print("\nGenerated files:")
    print("  Docs: 3 files")
    print("  Examples: 4 files")
    print("  Skeleton code: 6 files")
    print("  Report: 1 file")
    print("  Total: 14 files created/updated")
    print("\nNext steps:")
    print("  1. Review docs/PHASE5_EBAY_EXECUTOR.md for full design")
    print("  2. Implement src/executor/ modules (price_calculator, category_resolver, etc.)")
    print("  3. Add unit tests for price calculation and category resolution")
    print("  4. Proceed to Phase 6: eBay API Integration & Live Listing")

if __name__ == "__main__":
    main()
