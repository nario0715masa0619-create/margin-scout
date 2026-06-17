import pandas as pd

df = pd.read_csv('output_operational_test/research_results.csv')
print('='*100)
print('📊 最終 research_results.csv サマリー')
print('='*100)
print(f'\n✅ 出力件数: {len(df)} 件')
print(f'✅ カラム数: {len(df.columns)} 個')
print(f'\n【カラム一覧】')
for i, col in enumerate(df.columns, 1):
    print(f'  {i:2}. {col}')

print(f'\n【サンプルデータ（先頭3件）】')
print(df.head(3).to_string())

if 'profit_margin_pct' in df.columns:
    print(f'\n【利益統計】')
    avg_margin = df['profit_margin_pct'].mean()
    max_margin = df['profit_margin_pct'].max()
    min_margin = df['profit_margin_pct'].min()
    print(f'  平均利益率: {avg_margin:.2f}%')
    print(f'  最高利益率: {max_margin:.2f}%')
    print(f'  最低利益率: {min_margin:.2f}%')

if 'profit_amount_jpy' in df.columns:
    profit_positive = (df['profit_amount_jpy'] > 0).sum()
    profit_negative = (df['profit_amount_jpy'] < 0).sum()
    print(f'  黒字件数: {profit_positive} 件')
    print(f'  赤字件数: {profit_negative} 件')

if 'source' in df.columns:
    print(f'\n【ソース別集計】')
    print(df['source'].value_counts())

print('\n' + '='*100)
