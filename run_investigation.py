import os
from pathlib import Path
import re

print('=' * 70)
print('【EBAY_ENV 使用箇所の完全調査】')
print('=' * 70)

# 1. .env から EBAY_ENV を確認
print('\n【1】.env ファイルの確認')
print('-' * 70)
env_path = Path('C:/Users/nario/.marginscount/.env')
ebay_env_value = None

if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            if 'EBAY_ENV' in line:
                ebay_env_value = line.split('=')[1].strip()
                print(f'✅ EBAY_ENV={ebay_env_value}')

# 2. コード内の EBAY_ENV 使用箇所を検索
print('\n【2】EBAY_ENV のコード内使用箇所')
print('-' * 70)

py_files = list(Path('src').rglob('*.py'))
ebay_env_usage = {}

for py_file in py_files:
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'EBAY_ENV' in line or ('getenv' in line and 'EBAY' in line) or 'sandbox' in line.lower() or 'api_mode' in line.lower():
                    if py_file not in ebay_env_usage:
                        ebay_env_usage[py_file] = []
                    ebay_env_usage[py_file].append((i+1, line.strip()))
    except:
        pass

for file_path in sorted(ebay_env_usage.keys()):
    print(f'\n📄 {file_path}')
    for line_num, line in ebay_env_usage[file_path]:
        print(f'   Line {line_num}: {line}')

# 3. auth_handler.py を詳しく確認
print('\n【3】auth_handler.py の詳細確認')
print('-' * 70)
auth_file = Path('src/ebay_integration/auth_handler.py')
if auth_file.exists():
    print(f'✅ ファイル存在: {auth_file}')
    with open(auth_file, 'r', encoding='utf-8') as f:
        content = f.read()
        # クラス定義を抽出
        if 'class' in content:
            for match in re.finditer(r'class\s+(\w+)', content):
                print(f'   クラス: {match.group(1)}')
        # 初期化メソッドを抽出
        if '__init__' in content:
            print('   ✅ __init__ メソッドあり')
        # API モード関連の処理
        if 'sandbox' in content.lower():
            print('   ✅ sandbox が参照されている')
        if 'EBAY_ENV' in content:
            print('   ✅ EBAY_ENV が使用されている')

# 4. browse_api_client.py を詳しく確認
print('\n【4】browse_api_client.py の詳細確認')
print('-' * 70)
browse_file = Path('src/ebay_integration/browse_api_client.py')
if browse_file.exists():
    print(f'✅ ファイル存在: {browse_file}')
    with open(browse_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'class' in content:
            for match in re.finditer(r'class\s+(\w+)', content):
                print(f'   クラス: {match.group(1)}')
        if 'sandbox' in content.lower():
            print('   ✅ sandbox が参照されている')
        if 'search_items' in content:
            print('   ✅ search_items メソッドあり')

# 5. config_adapters.py を詳しく確認
print('\n【5】config_adapters.py の詳細確認')
print('-' * 70)
config_file = Path('src/source_adapters/config_adapters.py')
if config_file.exists():
    print(f'✅ ファイル存在: {config_file}')
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 'EBAY' in line or 'sandbox' in line.lower() or 'api' in line.lower():
                print(f'   Line {i+1}: {line.strip()}')

# 6. eBay API エンドポイントの確認
print('\n【6】eBay API エンドポイント（Sandbox vs Live）')
print('-' * 70)
print('   Sandbox: https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search')
print('   Live: https://api.ebay.com/buy/browse/v1/item_summary/search')

for py_file in py_files:
    try:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'api.sandbox.ebay.com' in content:
                print(f'   ✅ Sandbox エンドポイント検出: {py_file}')
            if 'api.ebay.com' in content and 'sandbox' not in content:
                print(f'   ✅ Live エンドポイント検出: {py_file}')
    except:
        pass

# 7. 結論
print('\n' + '=' * 70)
print('【結論】')
print('=' * 70)
print(f'✅ 現在の EBAY_ENV: {ebay_env_value}')
print('✅ EBAY_ENV の使用状況: 上記で確認')
print('次のステップ: Browse API 実接続確認テスト実行可能')
