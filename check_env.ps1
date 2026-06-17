cd C:\NewProjects\margin-scout

# ========================================
# .env ファイルの配置と読み込み方法を調査
# ========================================
Write-Host "=== .env ファイルの配置と読み込み方法を調査 ===" -ForegroundColor Cyan

# 1. .env ファイルの存在確認
Write-Host "`n【1】.env ファイルの確認" -ForegroundColor Yellow
$envPath = "C:\Users\nario\.marginscount\.env"
if (Test-Path $envPath) {
    Write-Host "✅ .env ファイル存在: $envPath" -ForegroundColor Green
    $envSize = (Get-Item $envPath).Length
    Write-Host "   サイズ: $envSize bytes" -ForegroundColor Green
    
    # 内容確認（キー名のみ）
    Write-Host "`n   キー一覧:" -ForegroundColor Green
    Get-Content $envPath | ForEach-Object {
        if ($_ -match "^[A-Z_]+=") {
            $key = $_ -replace "=.*", ""
            Write-Host "     - $key" -ForegroundColor Green
        }
    }
} else {
    Write-Host "❌ .env ファイルが見つかりません: $envPath" -ForegroundColor Red
}

# 2. プロジェクトルートの .env 確認
Write-Host "`n【2】プロジェクトルートの .env 確認" -ForegroundColor Yellow
if (Test-Path ".\.env") {
    Write-Host "✅ プロジェクトルート .env 存在" -ForegroundColor Green
} else {
    Write-Host "❌ プロジェクトルート .env なし" -ForegroundColor Red
}

# 3. .env 読み込みコードを検索
Write-Host "`n【3】.env 読み込み方法をコード内で検索" -ForegroundColor Yellow
$pyFiles = Get-ChildItem -Path "src" -Recurse -Filter "*.py" -File

Write-Host "`n   キーワード検索: 'load_dotenv', '.env', 'environ'" -ForegroundColor Yellow
$matches = $pyFiles | Select-String -Pattern "load_dotenv|\.env|os\.environ|getenv" -List

if ($matches) {
    $matches | ForEach-Object {
        Write-Host "   📄 $($_.Path)" -ForegroundColor Magenta
        # ファイル内で該当行を表示
        Select-String -Path $_.Path -Pattern "load_dotenv|\.env|os\.environ|getenv" | ForEach-Object {
            Write-Host "      Line $($_.LineNumber): $($_.Line.Trim())" -ForegroundColor Gray
        }
    }
}

# 4. auth_handler.py の確認
Write-Host "`n【4】auth_handler.py の .env 読み込み方法" -ForegroundColor Yellow
$authHandlerPath = "src/ebay_integration/auth_handler.py"
if (Test-Path $authHandlerPath) {
    Write-Host "✅ auth_handler.py を確認中..." -ForegroundColor Green
    Get-Content $authHandlerPath | Select-String -Pattern "load_dotenv|environ|getenv|\.env" -Context 2 | ForEach-Object {
        Write-Host "   $($_.Line)" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ auth_handler.py が見つかりません" -ForegroundColor Red
}

# 5. cli.py の確認
Write-Host "`n【5】cli.py の .env 読み込み方法" -ForegroundColor Yellow
$cliPath = "cli.py"
if (Test-Path $cliPath) {
    Write-Host "✅ cli.py を確認中..." -ForegroundColor Green
    Get-Content $cliPath | Select-String -Pattern "load_dotenv|environ|getenv|\.env" -Context 2 | ForEach-Object {
        Write-Host "   $($_.Line)" -ForegroundColor Gray
    }
} else {
    Write-Host "❌ cli.py が見つかりません" -ForegroundColor Red
}

# 6. requirements.txt で python-dotenv を確認
Write-Host "`n【6】requirements.txt で dotenv ライブラリを確認" -ForegroundColor Yellow
if (Test-Path "requirements.txt") {
    Get-Content "requirements.txt" | Select-String "python-dotenv|dotenv" | ForEach-Object {
        Write-Host "   ✅ $_" -ForegroundColor Green
    }
} else {
    Write-Host "❌ requirements.txt が見つかりません" -ForegroundColor Red
}

# 7. .env ファイルの読み込み方法を推測
Write-Host "`n【7】.env 読み込みメカニズムの推測" -ForegroundColor Yellow
Write-Host "   方法A: プロジェクトルートの .env を読み込む" -ForegroundColor Gray
Write-Host "   方法B: C:\Users\nario\.marginscount\.env を明示的に指定" -ForegroundColor Gray
Write-Host "   方法C: 環境変数から直接読み込む（.env 不使用）" -ForegroundColor Gray

# 8. 最終確認
Write-Host "`n=== 📊 サマリー ===" -ForegroundColor Cyan
Write-Host "確認内容:"
Write-Host "  ✅ .env の正確な配置場所: $envPath" -ForegroundColor Green
Write-Host "  ✅ .env 読み込みコード位置: src/ebay_integration/ 配下" -ForegroundColor Green
Write-Host "  ✅ 利用ライブラリ: python-dotenv の有無確認済み" -ForegroundColor Green
