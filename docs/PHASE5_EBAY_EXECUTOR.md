# Phase 5: eBay Executor & Dry-Run Implementation Design

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
