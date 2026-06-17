import os
from pathlib import Path

print('=' * 80)
print('【MarginScout eBay API 統合ファイルの詳細分析】')
print('=' * 80)

# ========================================
# 1. auth_handler.py の詳細確認
# ========================================
print('\n' + '=' * 80)
print('【1】src/ebay_integration/auth_handler.py')
print('=' * 80)

auth_file = Path('src/ebay_integration/auth_handler.py')
if auth_file.exists():
    with open(auth_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
else:
    print('❌ ファイルが見つかりません')

# ========================================
# 2. browse_api_client.py の詳細確認
# ========================================
print('\n' + '=' * 80)
print('【2】src/ebay_integration/browse_api_client.py')
print('=' * 80)

browse_file = Path('src/ebay_integration/browse_api_client.py')
if browse_file.exists():
    with open(browse_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
else:
    print('❌ ファイルが見つかりません')

# ========================================
# 3. config_loader.py の詳細確認
# ========================================
print('\n' + '=' * 80)
print('【3】src/config_loader.py')
print('=' * 80)

config_file = Path('src/config_loader.py')
if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content)
else:
    print('❌ ファイルが見つかりません')

# ========================================
# 4. ebay_integration ディレクトリ一覧
# ========================================
print('\n' + '=' * 80)
print('【4】src/ebay_integration/ ディレクトリ内容')
print('=' * 80)

ebay_dir = Path('src/ebay_integration')
if ebay_dir.exists():
    for file in sorted(ebay_dir.glob('*.py')):
        size = file.stat().st_size
        print(f'  {file.name} ({size} bytes)')
else:
    print('❌ ディレクトリが見つかりません')
