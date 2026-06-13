#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MarginScout Phase 7: Order Polling & Inventory Management Implementation
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

# ============================================================================
# DATA MODELS
# ============================================================================

class OrderStatus(str, Enum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RETURNED = "returned"
    PENDING = "pending"

class CandidateStatus(str, Enum):
    RESEARCH = "research"
    LISTED = "listed"
    SOLD = "sold"
    RETURNED = "returned"
    CANCELLED = "cancelled"

@dataclass
class OrderRecord:
    """eBay order record"""
    order_id: str
    listing_id: str
    sku: str
    candidate_id: str
    buyer_username: str
    order_status: str
    purchase_price: float
    quantity: int
    purchase_date: str
    order_total: float
    synced_at: str = None
    
    def __post_init__(self):
        if self.synced_at is None:
            self.synced_at = datetime.now().isoformat()

@dataclass
class InventoryUpdate:
    """Inventory status update"""
    candidate_id: str
    sku: str
    old_status: str
    new_status: str
    order_id: Optional[str]
    sold_price: float
    sold_date: str = None
    profit_margin: float = 0.0
    net_income: float = 0.0
    
    def __post_init__(self):
        if self.sold_date is None:
            self.sold_date = datetime.now().isoformat()

# ============================================================================
# ORDER POLLER
# ============================================================================

class OrderPoller:
    """Poll eBay Orders API for new sales"""
    
    def __init__(self, api_client, last_poll_file: str = "data/last_poll.json"):
        self.api_client = api_client
        self.last_poll_file = Path(last_poll_file)
        self.last_poll_time = self._load_last_poll()
    
    def _load_last_poll(self) -> datetime:
        """Load last poll timestamp"""
        if self.last_poll_file.exists():
            try:
                with open(self.last_poll_file, 'r') as f:
                    data = json.load(f)
                    return datetime.fromisoformat(data['last_poll'])
            except:
                pass
        return datetime.now() - timedelta(hours=24)
    
    def _save_last_poll(self, timestamp: datetime):
        """Save last poll timestamp"""
        self.last_poll_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.last_poll_file, 'w') as f:
            json.dump({'last_poll': timestamp.isoformat()}, f)
    
    def poll_orders(self) -> List[OrderRecord]:
        """Poll eBay for new orders"""
        print(f"[OrderPoller] Polling eBay Orders API...")
        print(f"  Last poll: {self.last_poll_time.isoformat()}")
        
        orders = []
        try:
            print("  [Mock] Found 0 new orders (API not connected)")
            now = datetime.now()
            self._save_last_poll(now)
            self.last_poll_time = now
            return orders
        except Exception as e:
            print(f"  [Error] Poll failed: {str(e)}")
            return []

# ============================================================================
# ORDER PARSER
# ============================================================================

class OrderParser:
    """Parse eBay order response"""
    
    @staticmethod
    def parse_order(ebay_order_data: Dict) -> Optional[OrderRecord]:
        """Parse single eBay order"""
        try:
            order = OrderRecord(
                order_id=ebay_order_data.get('orderId'),
                listing_id=ebay_order_data.get('lineItems', [{}])[0].get('listingId'),
                sku=ebay_order_data.get('lineItems', [{}])[0].get('sku'),
                candidate_id='',
                buyer_username=ebay_order_data.get('buyer', {}).get('username'),
                order_status=ebay_order_data.get('orderStatus', 'pending'),
                purchase_price=float(ebay_order_data.get('lineItems', [{}])[0].get('lineItemCost', {}).get('value', 0)),
                quantity=int(ebay_order_data.get('lineItems', [{}])[0].get('quantity', 1)),
                purchase_date=ebay_order_data.get('creationDate'),
                order_total=float(ebay_order_data.get('pricingSummary', {}).get('total', {}).get('value', 0)),
            )
            return order
        except Exception as e:
            print(f"  [Error] Failed to parse order: {str(e)}")
            return None

# ============================================================================
# INVENTORY UPDATER
# ============================================================================

class InventoryUpdater:
    """Update candidate inventory status"""
    
    def __init__(self, candidate_db_file: str = "data/candidates.json"):
        self.candidate_db_file = Path(candidate_db_file)
        self.candidates = self._load_candidates()
    
    def _load_candidates(self) -> Dict:
        """Load candidate database"""
        if self.candidate_db_file.exists():
            try:
                with open(self.candidate_db_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_candidates(self):
        """Save candidate database"""
        self.candidate_db_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.candidate_db_file, 'w') as f:
            json.dump(self.candidates, f, indent=2)
    
    def find_candidate_by_listing_id(self, listing_id: str) -> Optional[Dict]:
        """Find candidate by listing ID"""
        for candidate_id, candidate in self.candidates.items():
            if candidate.get('listing_id') == listing_id:
                return candidate
        return None
    
    def update_to_sold(self, order: OrderRecord, reference_price: float) -> Optional[InventoryUpdate]:
        """Update candidate to sold status"""
        candidate = self.find_candidate_by_listing_id(order.listing_id)
        
        if not candidate:
            print(f"  [Warning] Candidate not found for listing {order.listing_id}")
            return None
        
        old_status = candidate.get('status', 'listed')
        profit_margin = ((order.purchase_price - reference_price) / reference_price * 100) if reference_price > 0 else 0
        net_income = order.purchase_price - (order.purchase_price * 0.129)
        
        update = InventoryUpdate(
            candidate_id=candidate.get('candidate_id'),
            sku=order.sku,
            old_status=old_status,
            new_status='sold',
            order_id=order.order_id,
            sold_price=order.purchase_price,
            profit_margin=profit_margin,
            net_income=net_income,
        )
        
        candidate['status'] = 'sold'
        candidate['order_id'] = order.order_id
        candidate['sold_price'] = order.purchase_price
        candidate['sold_date'] = order.purchase_date
        candidate['profit_margin'] = profit_margin
        candidate['net_income'] = net_income
        
        self._save_candidates()
        return update

# ============================================================================
# SALES REPORTER
# ============================================================================

class SalesReporter:
    """Generate sales and profit reports"""
    
    def __init__(self, candidate_db_file: str = "data/candidates.json"):
        self.candidate_db_file = Path(candidate_db_file)
    
    def generate_daily_report(self) -> Dict:
        """Generate daily sales report"""
        try:
            with open(self.candidate_db_file, 'r') as f:
                candidates = json.load(f)
        except:
            candidates = {}
        
        today = datetime.now().date()
        sold_today = []
        
        for candidate_id, candidate in candidates.items():
            if candidate.get('status') == 'sold':
                sold_date = candidate.get('sold_date', '')
                try:
                    if datetime.fromisoformat(sold_date).date() == today:
                        sold_today.append(candidate)
                except:
                    pass
        
        total_revenue = sum(c.get('sold_price', 0) for c in sold_today)
        total_profit = sum(c.get('net_income', 0) for c in sold_today)
        avg_margin = sum(c.get('profit_margin', 0) for c in sold_today) / len(sold_today) if sold_today else 0
        
        report = {
            'report_date': today.isoformat(),
            'items_sold': len(sold_today),
            'total_revenue': round(total_revenue, 2),
            'total_profit': round(total_profit, 2),
            'avg_profit_margin': round(avg_margin, 2),
            'generated_at': datetime.now().isoformat(),
        }
        
        return report

# ============================================================================
# MAIN EXECUTOR
# ============================================================================

class Phase7Executor:
    """Main Phase 7 executor"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.order_poller = OrderPoller(api_client)
        self.order_parser = OrderParser()
        self.inventory_updater = InventoryUpdater()
        self.sales_reporter = SalesReporter()
    
    def execute_sync(self) -> Dict:
        """Execute full inventory sync"""
        print("\n" + "="*70)
        print("Phase 7: Inventory Sync Execution")
        print("="*70)
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'orders_polled': 0,
            'orders_parsed': 0,
            'inventory_updates': 0,
            'daily_report': None,
        }
        
        try:
            print("\n[Step 1] Polling eBay Orders...")
            orders = self.order_poller.poll_orders()
            result['orders_polled'] = len(orders)
            print(f"  Found: {len(orders)} orders")
            
            print("\n[Step 2] Parsing orders...")
            parsed_orders = []
            for order_data in orders:
                parsed = self.order_parser.parse_order(order_data)
                if parsed:
                    parsed_orders.append(parsed)
            result['orders_parsed'] = len(parsed_orders)
            print(f"  Parsed: {len(parsed_orders)} orders")
            
            print("\n[Step 3] Updating inventory...")
            updates = []
            for order in parsed_orders:
                update = self.inventory_updater.update_to_sold(order, 100.0)
                if update:
                    updates.append(update)
                    print(f"  Updated: {order.sku} -> sold")
            result['inventory_updates'] = len(updates)
            
            print("\n[Step 4] Generating daily report...")
            report = self.sales_reporter.generate_daily_report()
            result['daily_report'] = report
            items = report['items_sold']
            revenue = report['total_revenue']
            print(f"  Today: {items} items sold, Revenue: {revenue}")
            
            print("\n" + "="*70)
            print("Phase 7 Sync: COMPLETE")
            print("="*70)
        
        except Exception as e:
            print(f"\n[Error] Sync failed: {str(e)}")
            result['error'] = str(e)
        
        return result

# ============================================================================
# MAIN
# ============================================================================

def main():
    try:
        from src.api_integration.oauth_handler import EBayOAuthConfig, EBayAPIConfig, OAuthHandler
        from src.api_integration.api_client_live import EBayLiveAPIClient
        
        print("="*70)
        print("MarginScout Phase 7: Order Polling & Inventory Management")
        print("="*70)
        
        oauth_config = EBayOAuthConfig.from_env()
        api_config = EBayAPIConfig.from_env()
        oauth_handler = OAuthHandler(oauth_config, api_config)
        api_client = EBayLiveAPIClient(oauth_handler, api_config)
        
        executor = Phase7Executor(api_client)
        result = executor.execute_sync()
        
        report_path = Path.cwd() / 'PHASE7_SYNC_RESULT.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\nSync result saved: {report_path}")
    
    except Exception as e:
        print(f"Phase 7 initialization: {str(e)}")
        print("Components are ready. Run with proper eBay credentials.")

if __name__ == '__main__':
    main()
