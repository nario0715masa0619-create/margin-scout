# eBay Category Mapping Specification

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
