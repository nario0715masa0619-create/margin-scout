import os
import sys

# Backend ディレクトリ作成
backend_dirs = [
    'margin-scout-backend',
    'margin-scout-backend/app',
    'margin-scout-backend/app/services',
    'margin-scout-backend/app/models',
    'margin-scout-backend/app/routes',
    'margin-scout-backend/logs',
]

for d in backend_dirs:
    os.makedirs(d, exist_ok=True)
    print(f"✅ ディレクトリ作成: {d}")

# requirements.txt 生成
requirements = '''fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
pytest==7.4.3
httpx==0.25.2
python-dotenv==1.0.0
aiofiles==23.2.1
'''

with open('margin-scout-backend/requirements.txt', 'w') as f:
    f.write(requirements)
    print("✅ requirements.txt 作成完了")

# venv 作成確認メッセージ
print("\n次のコマンドで仮想環境を作成してください:")
print("  Windows: python -m venv venv_backend")
print("  macOS/Linux: python3 -m venv venv_backend")
print("\nアクティベート後:")
print("  pip install -r margin-scout-backend/requirements.txt")
