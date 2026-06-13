#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 3～5 Implementation
Implements CSV conversion, validation, payload building, and dry-run execution.
"""

import os
import json
import csv
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import hashlib
import math

# ============================================================================
# PHASE 3: CSV Integration - Implementation
# ============================================================================

class ConditionEnum(str, Enum):
    NEW = "new"
    LIKE_NEW = "like_new"
    GOOD = "good"
    FAIR = "fair"
    FOR_PARTS = "for_parts_or_not_working"

class ValidationStatus(str, Enum):
    HARD_ERROR = "hard_error"
    SOFT_WARNING = "soft_warning"
    READY = "ready"
    PENDING_REVIEW = "pending_review"

@dataclass
class ResearchRow:
    """Row from research CSV (Layer 0)"""
    candidate_id: str
    product_name: str
    reference_price: float
    currency: str
    brand: str
    model_number: str
    category: str
    product_url: str
    source_type: str
    observed_date: str
    condition: str
    user_notes: str
    user_tags: str
    judgement_flag: str
    research_status: str

@dataclass
class ListingRecord:
    """Listing-ready record (Layer 3 from Phase 3)"""
    candidate_id: str
    sku: str
    title: str
    description: str
    category: str
    condition: str
    price: float
    quantity: int
    images: List[str]
    brand: str
    model_number: str
    product_url: str
    user_notes: str
    user_tags: str
    source_url: str
    reference_price: float
    created_at: str

class CSVMapper:
    """Maps Research CSV to Listing Record"""
    
    @staticmethod
    def generate_sku(candidate_id: str) -> str:
        """Generate SKU: MARGIN-YYYYMMDD-NNNN"""
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        # Extract number from candidate_id
        num_part = ''.join(filter(str.isdigit, candidate_id[-4:])) or "0001"
        return f"MARGIN-{date_str}-{num_part.zfill(4)}"
    
    @staticmethod
    def generate_title(brand: str, model: str, category: str) -> str:
        """Generate title: [Brand] [Model] - [Category snippet]"""
        title = f"{brand} {model}".strip()
        if len(title) > 80:
            title = title[:77] + "..."
        return title
    
    @staticmethod
    def generate_description(product_name: str, brand: str, condition: str, user_notes: str) -> str:
        """Generate description from product info"""
        desc = f"{product_name}\n\n"
        desc += f"Brand: {brand}\n"
        desc += f"Condition: {condition}\n"
        if user_notes:
            desc += f"\nNotes: {user_notes}\n"
        desc += "\nThis item has been researched and is ready for sale."
        if len(desc) > 4000:
            desc = desc[:3997] + "..."
        return desc
    
    @classmethod
    def map_research_row_to_listing(cls, research_row: ResearchRow) -> ListingRecord:
        """Convert research row to listing record"""
        sku = cls.generate_sku(research_row.candidate_id)
        title = cls.generate_title(research_row.brand, research_row.model_number, research_row.category)
        description = cls.generate_description(
            research_row.product_name,
            research_row.brand,
            research_row.condition,
            research_row.user_notes
        )
        
        # Default images (to be resolved in Phase 4)
        images = []
        
        listing = ListingRecord(
            candidate_id=research_row.candidate_id,
            sku=sku,
            title=title,
            description=description,
            category=research_row.category,
            condition=research_row.condition,
            price=research_row.reference_price,  # Placeholder, will be calculated in Phase 5
            quantity=1,
            images=images,
            brand=research_row.brand,
            model_number=research_row.model_number,
            product_url=research_row.product_url,
            user_notes=research_row.user_notes,
            user_tags=research_row.user_tags,
            source_url=research_row.product_url,
            reference_price=research_row.reference_price,
            created_at=datetime.now().isoformat()
        )
        return listing

class CSVValidator:
    """4-stage validation for listing records"""
    
    HARD_ERRORS_LIST = [
        "missing_title",
        "missing_price",
        "missing_category",
        "missing_condition",
        "title_too_long",
        "price_out_of_range",
        "invalid_condition",
    ]
    
    SOFT_WARNINGS_LIST = [
        "title_near_limit",
        "missing_notes",
        "no_images",
    ]
    
    @classmethod
    def validate(cls, listing: ListingRecord) -> Dict:
        """Validate listing record"""
        errors = []
        warnings = []
        
        # Hard errors
        if not listing.title or listing.title.strip() == "":
            errors.append("missing_title")
        if len(listing.title) > 80:
            errors.append("title_too_long")
        if listing.price <= 0 or listing.price > 999999.99:
            errors.append("price_out_of_range")
        if not listing.category or listing.category.strip() == "":
            errors.append("missing_category")
        valid_conditions = [c.value for c in ConditionEnum]
        if not listing.condition or listing.condition not in valid_conditions:
            errors.append("invalid_condition")
        
        # Soft warnings
        if len(listing.title) > 70:
            warnings.append("title_near_limit")
        if not listing.user_notes:
            warnings.append("missing_notes")
        if not listing.images:
            warnings.append("no_images")
        
        # Determine status
        if errors:
            status = ValidationStatus.HARD_ERROR
        elif warnings:
            status = ValidationStatus.SOFT_WARNING
        else:
            status = ValidationStatus.READY
        
        # Calculate score
        total_checks = len(cls.HARD_ERRORS_LIST) + len(cls.SOFT_WARNINGS_LIST)
        passed_checks = total_checks - len(errors) - len(warnings)
        score = passed_checks / total_checks if total_checks > 0 else 1.0
        
        return {
            "hard_errors": errors,
            "soft_warnings": warnings,
            "validation_status": status.value,
            "overall_score": round(score, 2),
        }

# ============================================================================
# PHASE 4: Payload Builder - Implementation
# ============================================================================

@dataclass
class EBayPayload:
    """Final eBay payload (Layer 4)"""
    sku: str
    title: str
    description: str
    price: float
    quantity: int
    condition: int  # 3000 or 7000
    category_id: int
    images: List[str]
    candidate_id: str
    source_url: str
    user_notes: str
    created_at: str

class ConditionMapper:
    """Map internal condition to eBay enum"""
    
    MAPPING = {
        ConditionEnum.NEW.value: 3000,
        ConditionEnum.LIKE_NEW.value: 3000,
        ConditionEnum.GOOD.value: 3000,
        ConditionEnum.FAIR.value: 7000,
        ConditionEnum.FOR_PARTS.value: 7000,
    }
    
    @classmethod
    def map_condition(cls, condition: str) -> int:
        """Map condition to eBay enum"""
        return cls.MAPPING.get(condition, 3000)

class CategoryResolver:
    """Resolve category to eBay Category ID"""
    
    # Simplified mapping
    CATEGORY_MAPPING = {
        "Electronics > Cameras > Lenses": 625,
        "Electronics > Cameras": 625,
        "Collectibles > Trading Cards": 39439,
        "Clothing & Accessories > Shoes": 63889,
    }
    
    @classmethod
    def resolve_category(cls, internal_category: str) -> Tuple[int, str]:
        """Resolve category to eBay ID and path"""
        # Try exact match
        if internal_category in cls.CATEGORY_MAPPING:
            cat_id = cls.CATEGORY_MAPPING[internal_category]
            return cat_id, internal_category
        
        # Try partial match
        for key, cat_id in cls.CATEGORY_MAPPING.items():
            if key in internal_category or internal_category in key:
                return cat_id, key
        
        # Fallback
        return 15687, "Miscellaneous"

class ImageMapper:
    """Resolve images from SKU-based directory"""
    
    @staticmethod
    def resolve_images(sku: str, base_dir: str = "data/images") -> List[str]:
        """Resolve images from data/images/{SKU}/ directory"""
        image_dir = Path(base_dir) / sku
        if not image_dir.exists():
            return []
        
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            for img_file in sorted(image_dir.glob(ext)):
                images.append(str(img_file))
                if len(images) >= 12:  # Max 12 images
                    break
        
        return images

class EBayPayloadBuilder:
    """Build final eBay payload from listing record"""
    
    @staticmethod
    def build(listing: ListingRecord) -> EBayPayload:
        """Build eBay payload from listing record"""
        # Map condition
        condition_ebay = ConditionMapper.map_condition(listing.condition)
        
        # Resolve category
        category_id, _ = CategoryResolver.resolve_category(listing.category)
        
        # Resolve images
        images = ImageMapper.resolve_images(listing.sku)
        
        payload = EBayPayload(
            sku=listing.sku,
            title=listing.title,
            description=listing.description,
            price=listing.price,
            quantity=listing.quantity,
            condition=condition_ebay,
            category_id=category_id,
            images=images,
            candidate_id=listing.candidate_id,
            source_url=listing.source_url,
            user_notes=listing.user_notes,
            created_at=listing.created_at,
        )
        
        return payload

# ============================================================================
# PHASE 5: Executor & Dry-Run - Implementation
# ============================================================================

class PriceCalculator:
    """Calculate final eBay price from reference price"""
    
    def __init__(self, margin_percent: float = 15.0, platform_fee_percent: float = 12.9):
        self.margin_percent = margin_percent
        self.platform_fee_percent = platform_fee_percent
    
    def calculate_price(self, reference_price: float) -> Tuple[float, Dict]:
        """Calculate final price and return log"""
        divisor = 1 - (self.margin_percent / 100) - (self.platform_fee_percent / 100)
        if divisor <= 0:
            raise ValueError("Invalid margin/fee configuration")
        
        calculated_price = reference_price / divisor
        
        # Round up to nearest cent
        calculated_price = math.ceil(calculated_price * 100) / 100
        
        # Validate bounds
        if calculated_price < 0.99 or calculated_price > 999999.99:
            raise ValueError(f"Calculated price {calculated_price} out of bounds")
        
        log = {
            "formula": "(reference_price) / (1 - margin% - fee%)",
            "reference_price": reference_price,
            "divisor": divisor,
            "calculated_price": calculated_price,
            "margin_percent": self.margin_percent,
            "platform_fee_percent": self.platform_fee_percent,
        }
        
        return calculated_price, log

class DryRunExecutor:
    """Execute dry-run simulation"""
    
    @staticmethod
    def execute_dry_run(payload: EBayPayload, price_calculator: PriceCalculator) -> Dict:
        """Execute dry-run and return mock response"""
        # Calculate final price
        final_price, price_log = price_calculator.calculate_price(payload.price)
        
        # Generate mock listing ID
        mock_listing_id = f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(payload.sku.encode()).hexdigest()[:8]}"
        
        # Calculate fees
        insertion_fee = 0.0
        final_value_fee = final_price * 0.129
        total_fee = insertion_fee + final_value_fee
        
        # Validation checks
        validation_errors = []
        if not payload.title:
            validation_errors.append("missing_title")
        if not payload.images:
            validation_errors.append("no_images")
        if payload.price <= 0:
            validation_errors.append("invalid_price")
        
        execution_valid = len(validation_errors) == 0
        next_action = "ready_for_phase_6" if execution_valid else "manual_review"
        
        return {
            "mock_listing_id": mock_listing_id,
            "sku": payload.sku,
            "status": "draft",
            "final_price": final_price,
            "insertion_fee": insertion_fee,
            "final_value_fee": final_value_fee,
            "total_fee": total_fee,
            "price_log": price_log,
            "validation_errors": validation_errors,
            "execution_valid": execution_valid,
            "next_action": next_action,
            "timestamp": datetime.now().isoformat(),
        }

# ============================================================================
# E2E Integration & Testing
# ============================================================================

def load_research_csv(csv_path: str) -> List[ResearchRow]:
    """Load research CSV"""
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            research_row = ResearchRow(
                candidate_id=row['candidate_id'],
                product_name=row['product_name'],
                reference_price=float(row['reference_price']),
                currency=row['currency'],
                brand=row['brand'],
                model_number=row['model_number'],
                category=row['category'],
                product_url=row['product_url'],
                source_type=row['source_type'],
                observed_date=row['observed_date'],
                condition=row['condition'],
                user_notes=row.get('user_notes', ''),
                user_tags=row.get('user_tags', ''),
                judgement_flag=row.get('judgement_flag', ''),
                research_status=row.get('research_status', 'active'),
            )
            rows.append(research_row)
    return rows

def run_e2e_dry_run(research_csv_path: str) -> Dict:
    """Run end-to-end dry-run"""
    print(f"Loading research CSV: {research_csv_path}")
    research_rows = load_research_csv(research_csv_path)
    print(f"Loaded {len(research_rows)} research rows")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_items": len(research_rows),
        "successful": 0,
        "failed": 0,
        "items": [],
    }
    
    price_calculator = PriceCalculator(margin_percent=15.0, platform_fee_percent=12.9)
    
    for research_row in research_rows:
        print(f"\nProcessing: {research_row.candidate_id}")
        
        try:
            # Phase 3: Map to listing
            print("  → Phase 3: Mapping research to listing...")
            listing = CSVMapper.map_research_row_to_listing(research_row)
            
            # Phase 3: Validate listing
            print("  → Phase 3: Validating listing...")
            validation_result = CSVValidator.validate(listing)
            print(f"    Validation status: {validation_result['validation_status']}")
            
            # Phase 4: Build payload
            print("  → Phase 4: Building eBay payload...")
            payload = EBayPayloadBuilder.build(listing)
            
            # Phase 5: Execute dry-run
            print("  → Phase 5: Executing dry-run...")
            dry_run_result = DryRunExecutor.execute_dry_run(payload, price_calculator)
            
            item_result = {
                "candidate_id": research_row.candidate_id,
                "sku": listing.sku,
                "validation": validation_result,
                "dry_run": dry_run_result,
                "status": "success" if dry_run_result["execution_valid"] else "warning",
            }
            
            results["items"].append(item_result)
            if dry_run_result["execution_valid"]:
                results["successful"] += 1
                print(f"  ✅ Success! Mock listing ID: {dry_run_result['mock_listing_id']}")
            else:
                results["failed"] += 1
                print(f"  ⚠️ Warning: {dry_run_result['validation_errors']}")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            results["failed"] += 1
            results["items"].append({
                "candidate_id": research_row.candidate_id,
                "status": "error",
                "error": str(e),
            })
    
    return results

def main():
    """Main execution"""
    project_dir = Path.cwd()
    research_csv = project_dir / "examples" / "research_sample.csv"
    
    if not research_csv.exists():
        print(f"Error: {research_csv} not found")
        return
    
    print("="*70)
    print("MarginScout: Phase 3～5 End-to-End Dry-Run Test")
    print("="*70)
    
    # Run E2E test
    results = run_e2e_dry_run(str(research_csv))
    
    # Save results
    report_path = project_dir / "IMPLEMENTATION_E2E_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print(f"E2E Test Complete: {results['successful']}/{results['total_items']} successful")
    print(f"Report saved: {report_path}")
    print("="*70)

if __name__ == "__main__":
    main()
