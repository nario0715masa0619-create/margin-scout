from src.research_workflow.profit_calculator_v2 import ProfitCalculatorV2

# テスト例
calc = ProfitCalculatorV2(exchange_rate=157.50)

examples = [
    {"name": "iPhone 16 ケース ¥1,000", "ebay_usd": 29.99, "source_jpy": 1000},
    {"name": "LG スピーカー ¥2,799", "ebay_usd": 29.99, "source_jpy": 2799},
    {"name": "Canon 5D ¥129,000", "ebay_usd": 29.99, "source_jpy": 129000},
    {"name": "高額商品 $200", "ebay_usd": 200.0, "source_jpy": 10000},
]

print("\n" + "=" * 80)
print("【正確な利益計算（eBay手数料 + 国際送料を含む）】")
print("=" * 80)

for ex in examples:
    result = calc.calculate_profit(ex["ebay_usd"], ex["source_jpy"])
    print(f"\n📦 {ex['name']}")
    print(f"  eBay 売却価格: ${result['ebay_price_usd']} = ¥{result['ebay_revenue_jpy']:,.0f}")
    print(f"  【支出】")
    print(f"    ├─ eBay 手数料: ¥{result['ebay_fvf_jpy']:,.0f}")
    print(f"    ├─ 国際送料: ¥{result['shipping_jpy']:,.0f}")
    print(f"    └─ 仕入れ価格: ¥{result['source_price_jpy']:,.0f}")
    print(f"    合計支出: ¥{result['total_expenses_jpy']:,.0f}")
    print(f"  ─────────────────────")
    print(f"  💰 利益: ¥{result['profit_jpy']:,.0f}")
    print(f"  📊 利益率: {result['profit_margin_pct']:.1f}%")
    
    if result['profit_jpy'] > 0:
        print(f"  ✅ 黒字（出品推奨）")
    elif result['profit_jpy'] > -2000:
        print(f"  ⚠️ 小赤字（検討要）")
    else:
        print(f"  ❌ 赤字（出品非推奨）")

print("\n" + "=" * 80)
