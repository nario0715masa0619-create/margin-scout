import os
from pathlib import Path

def print_context(file_path: str, pattern: list, context: int = 3):
    p = Path(file_path)
    if not p.exists():
        print(f"❌ File not found: {file_path}")
        return
        
    with open(p, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    matches = []
    for i, line in enumerate(lines):
        if any(pat in line for pat in pattern):
            matches.append(i)
            
    if not matches:
        print(f"No matches found for {pattern} in {file_path}")
        return
        
    printed = set()
    for m in matches:
        start = max(0, m - context)
        end = min(len(lines), m + context + 1)
        print(f"\n--- Match at line {m+1} ---")
        for i in range(start, end):
            if i not in printed:
                prefix = "> " if i == m else "  "
                print(f"{i+1:03d} {prefix}{lines[i].rstrip()}")
                printed.add(i)

print('=' * 80)
print('【互換性確認】')
print('=' * 80)

print('\n【1】research_processor_with_sources.py の使用パターン確認')
print('-' * 80)
print_context('src/research_workflow/research_processor_with_sources.py', ['EbayBrowseApiClient', 'auth_handler', 'EbayAuthHandler'])

print('\n【2】test_operational_multicat_nonmock.py の使用パターン確認')
print('-' * 80)
print_context('test_operational_multicat_nonmock.py', ['EbayBrowseApiClient', 'auth_handler', 'EbayAuthHandler'])
