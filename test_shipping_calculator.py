from src.research_workflow.shipping_calculator import ShippingCalculator

calc = ShippingCalculator(exchange_rate=157.50)

print("\n" + "=" * 80)
print("【送料計算テスト】")
print("=" * 80)

test_cases = [
    {"name": "iPhone ケース (200g)", "weight_g": 200},
    {"name": "デジカメ (800g)", "weight_g": 800},
    {"name": "Canon レンズ (1500g)", "weight_g": 1500},
    {"name": "高額商品 (5000g)", "weight_g": 5000},
]

for case in test_cases:
    print(f"\n📦 {case['name']}")
    result = calc.get_optimal_shipping(case["weight_g"])
    print(f"  キャリア: {result['carrier']}")
    print(f"  重さ: {case['weight_g']}g → 送料: ¥{result['shipping_jpy']:,.0f} (${result['shipping_usd']:.2f})")
    print(f"  配達日数: {result['estimated_days']} 日")

print("\n" + "=" * 80)
