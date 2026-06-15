from src.research_workflow.profit_calculator_v2 import ProfitCalculatorV2

calc = ProfitCalculatorV2(exchange_rate=157.50)

print("\n" + "=" * 80)
print("【統合テスト: 利益計算 + 正確な送料】")
print("=" * 80)

examples = [
    {"name": "iPhone ケース $30", "ebay_usd": 30, "source_jpy": 1000, "weight_g": 200, "category": "electronics"},
    {"name": "デジカメ $150", "ebay_usd": 150, "source_jpy": 50000, "weight_g": 800, "category": "camera"},
    {"name": "Canon レンズ $200", "ebay_usd": 200, "source_jpy": 80000, "weight_g": 1500, "category": "camera"},
    {"name": "高額商品 $500", "ebay_usd": 500, "source_jpy": 100000, "weight_g": 2000, "category": "electronics"},
]

for ex in examples:
    result = calc.calculate_profit(ex["ebay_usd"], ex["source_jpy"], ex.get("weight_g"), ex.get("category"))
    
    print(f"\n📦 {ex['name']}")
    print(f"  【収入】")
    print(f"    eBay 売却: ${result['ebay_price_usd']} = ¥{result['ebay_revenue_jpy']:,.0f}")
    print(f"  【支出】")
    print(f"    ├─ eBay 手数料: ¥{result['ebay_fvf_jpy']:,.0f}")
    print(f"    ├─ 送料 ({result['shipping_carrier']}): ¥{result['shipping_jpy']:,.0f}")
    print(f"    └─ 仕入れ: ¥{result['source_price_jpy']:,.0f}")
    print(f"    合計: ¥{result['total_expenses_jpy']:,.0f}")
    print(f"  ─────────────────────")
    print(f"  💰 利益: ¥{result['profit_jpy']:,.0f}")
    print(f"  📊 利益率: {result['profit_margin_pct']:.1f}%")
    
    if result['profit_jpy'] > 0:
        print(f"  ✅ 黒字（出品推奨）")
    else:
        print(f"  ❌ 赤字（出品非推奨）")

print("\n" + "=" * 80)
