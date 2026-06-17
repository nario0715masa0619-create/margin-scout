# ============================================================================
# error_injection_helper.py
# ============================================================================
# 目的: Day 4 タイムアウト注入のヘルパースクリプト
# 使用方法:
#   python error_injection_helper.py --inject timeout  # sleep(35) を追加
#   python error_injection_helper.py --revert          # 削除して元に戻す
# ============================================================================

import sys
import re
from pathlib import Path

BACKEND_MAIN = Path("margin-scout-backend/app/main.py")
TIMEOUT_MARKER = "# [ERROR_INJECTION_TIMEOUT_START]"
TIMEOUT_CODE = """
    # [ERROR_INJECTION_TIMEOUT_START]
    import asyncio
    await asyncio.sleep(35)  # Force timeout (threshold: 30s)
    # [ERROR_INJECTION_TIMEOUT_END]
"""

def inject_timeout():
    """POST /api/research/jobs に sleep(35) を挿入"""
    if not BACKEND_MAIN.exists():
        print(f"❌ エラー: {BACKEND_MAIN} が見つかりません")
        return False
    
    content = BACKEND_MAIN.read_text(encoding='utf-8')
    
    # 既に挿入されているか確認
    if TIMEOUT_MARKER in content:
        print("⚠️  タイムアウト注入コードは既に存在します")
        return False
    
    # POST /api/research/jobs エンドポイント内の最初の行に挿入
    pattern = r'(@app\.post\("/api/research/jobs"\)\nasync def start_job.*?:\n)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("❌ エラー: POST /api/research/jobs が見つかりません")
        return False
    
    insertion_point = match.end()
    new_content = content[:insertion_point] + TIMEOUT_CODE + content[insertion_point:]
    
    BACKEND_MAIN.write_text(new_content, encoding='utf-8')
    print("✅ タイムアウト注入完了")
    print("   Backend を再起動してください: python -m uvicorn app.main:app --reload")
    return True

def revert_timeout():
    """sleep(35) コードを削除"""
    if not BACKEND_MAIN.exists():
        print(f"❌ エラー: {BACKEND_MAIN} が見つかりません")
        return False
    
    content = BACKEND_MAIN.read_text(encoding='utf-8')
    
    if TIMEOUT_MARKER not in content:
        print("⚠️  タイムアウト注入コードは存在しません")
        return False
    
    # [ERROR_INJECTION_TIMEOUT_START] ～ [ERROR_INJECTION_TIMEOUT_END] を削除
    pattern = r'\s*# \[ERROR_INJECTION_TIMEOUT_START\].*?# \[ERROR_INJECTION_TIMEOUT_END\]\n'
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)
    
    BACKEND_MAIN.write_text(new_content, encoding='utf-8')
    print("✅ タイムアウト注入コードを削除しました")
    print("   Backend を再起動してください: python -m uvicorn app.main:app --reload")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python error_injection_helper.py [--inject|--revert]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "--inject":
        inject_timeout()
    elif cmd == "--revert":
        revert_timeout()
    else:
        print(f"❌ 不明なコマンド: {cmd}")
        sys.exit(1)
