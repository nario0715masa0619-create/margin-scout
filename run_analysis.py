import json
import csv
from pathlib import Path
from collections import defaultdict

# ========================================
# 1. テスト結果ファイルのロード
# ========================================
report_path = Path('output_operational_test/test_report.json')
csv_path = Path('output_operational_test/research_results.csv')

if not report_path.exists():
    print('❌ test_report.json not found. Run operational test first.')
    exit(1)

with open(report_path, encoding='utf-8') as f:
    report = json.load(f)

# ========================================
# 2. 失敗分類（Failure Reason Breakdown）
# ========================================
print('=' * 60)
print('【Step 1】失敗ケース分類')
print('=' * 60)

failure_reasons = report.get('failure_reasons', {})
total_failures = sum(failure_reasons.values())

print(f'\n総入力件数: {report["summary"]["total_inputs"]}')
print(f'総成功件数: {report["summary"]["csv_output_count"]}')
print(f'総失敗件数: {total_failures}')

print(f'\n失敗理由の内訳:')
for reason, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True):
    pct = (count / total_failures * 100) if total_failures > 0 else 0
    print(f'  {reason}: {count} 件 ({pct:.1f}%)')

# ========================================
# 3. ソース別成功率
# ========================================
print('\n' + '=' * 60)
print('【Step 2】ソース別成功率')
print('=' * 60)

source_stats = report.get('source_adapters', {})
print('\nソース別統計:')
for source, stats in source_stats.items():
    items = stats.get('items_found', 0)
    success_rate = stats.get('success_rate_pct', 0)
    print(f'  {source}:')
    print(f'    - 取得件数: {items}')
    print(f'    - 成功率: {success_rate:.1f}%')

# ========================================
# 4. CSV から結果データを読み込み
# ========================================
print('\n' + '=' * 60)
print('【Step 3】カテゴリ・キーワード別成功率分析')
print('=' * 60)

results_by_category = defaultdict(list)
results_by_keyword = defaultdict(list)
results_by_source = defaultdict(list)

if csv_path.exists():
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # CSV スキーマを確認
            category = row.get('category', 'unknown')
            keyword = row.get('keyword', 'unknown')
            source = row.get('source_channel', 'unknown')
            
            results_by_category[category].append(row)
            results_by_keyword[keyword].append(row)
            results_by_source[source].append(row)

    print('\nカテゴリ別成功率:')
    for category, rows in sorted(results_by_category.items()):
        print(f'  {category}: {len(rows)} 件')

    print('\nキーワード別成功率:')
    for keyword, rows in sorted(results_by_keyword.items()):
        print(f'  {keyword}: {len(rows)} 件')

    print('\nソース別成功件数（CSV 出力ベース）:')
    for source, rows in sorted(results_by_source.items()):
        print(f'  {source}: {len(rows)} 件')

# ========================================
# 5. 利益率分布
# ========================================
print('\n' + '=' * 60)
print('【Step 4】利益率分布')
print('=' * 60)

profit_margins = []
profitable_count = 0
loss_count = 0
neutral_count = 0

if csv_path.exists():
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                margin = float(row.get('profit_margin_pct', 0))
                profit_margins.append(margin)
                
                if margin > 0:
                    profitable_count += 1
                elif margin < 0:
                    loss_count += 1
                else:
                    neutral_count += 1
            except ValueError:
                pass

    if profit_margins:
        avg_margin = sum(profit_margins) / len(profit_margins)
        min_margin = min(profit_margins)
        max_margin = max(profit_margins)
        
        print(f'\n利益率統計:')
        print(f'  平均: {avg_margin:.2f}%')
        print(f'  最小: {min_margin:.2f}%')
        print(f'  最大: {max_margin:.2f}%')
        print(f'  黒字件数: {profitable_count} 件')
        print(f'  赤字件数: {loss_count} 件')
        print(f'  中立件数: {neutral_count} 件')

# ========================================
# 6. サンプル結果の表示
# ========================================
print('\n' + '=' * 60)
print('【Step 5】サンプル結果（先頭 5 件）')
print('=' * 60)

if csv_path.exists():
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 5:
                break
            print(f'\n[{i+1}] {row.get("product_name", "N/A")}')
            print(f'  ソース: {row.get("source_channel")} | 価格: ¥{row.get("source_price_jpy")}')
            print(f'  eBay 価格: ${row.get("ebay_price_usd")} | 利益率: {row.get("profit_margin_pct")}%')
            print(f'  URL: {row.get("source_url")}')

print('\n' + '=' * 60)
print('✅ 分析完了')
print('=' * 60)
