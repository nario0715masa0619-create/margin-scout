cd C:\NewProjects\margin-scout

# ========================================
# Step 1: メール通知関連ファイルを特定
# ========================================
Write-Host "=== Step 1: メール通知関連ファイルの確認 ===" -ForegroundColor Cyan
$emailFiles = @(
    "src/research_workflow/email_notifier.py",
    "src/research_workflow/notifier.py"
)

foreach ($file in $emailFiles) {
    if (Test-Path $file) {
        Write-Host "❌ 削除候補: $file" -ForegroundColor Red
        Get-Item $file | Select FullName, Length
    }
}

# ========================================
# Step 2: デプロイスクリプトをスキャン
# ========================================
Write-Host "`n=== Step 2: デプロイスクリプト内のメール処理を検索 ===" -ForegroundColor Cyan
$deployFiles = @("deploy_windows.bat", "deploy_linux.sh")

foreach ($file in $deployFiles) {
    if (Test-Path $file) {
        Write-Host "`n📄 $file:" -ForegroundColor Yellow
        Select-String -Path $file -Pattern "email|mail|notif" -CaseSensitive
    }
}

# ========================================
# Step 3: Pythonコード内の仕様外機能を検索
# ========================================
Write-Host "`n=== Step 3: Pythonコード内の仕様外キーワード検索 ===" -ForegroundColor Cyan

$scopeOutKeywords = @{
    "email|mail|notif" = "メール通知";
    "scheduler|cron|task|daemon" = "定期配信/スケジューラー";
    "Sell|Inventory|Order" = "Sell API/在庫/注文";
    "listing|upload.*ebay" = "出品実行";
    "database|sqlite|db\." = "DB永続化";
}

$pythonFiles = Get-ChildItem -Path "src" -Recurse -Filter "*.py" -File

foreach ($keyword in $scopeOutKeywords.Keys) {
    $matches = $pythonFiles | Select-String -Pattern $keyword -List
    if ($matches) {
        Write-Host "`n🔍 キーワード『$keyword』→『$($scopeOutKeywords[$keyword])』:" -ForegroundColor Yellow
        $matches | ForEach-Object {
            Write-Host "   - $($_.Path)" -ForegroundColor Red
        }
    }
}

# ========================================
# Step 4: ドキュメント内の矛盾を検索
# ========================================
Write-Host "`n=== Step 4: ドキュメント内の矛盾検索 ===" -ForegroundColor Cyan

$docFiles = Get-ChildItem -Path "docs", "." -Filter "*.md" -File -ErrorAction SilentlyContinue

foreach ($keyword in $scopeOutKeywords.Keys) {
    $matches = $docFiles | Select-String -Pattern $keyword -List
    if ($matches) {
        Write-Host "`n📝 キーワード『$keyword』→『$($scopeOutKeywords[$keyword])』:" -ForegroundColor Yellow
        $matches | ForEach-Object {
            Write-Host "   - $($_.Path)" -ForegroundColor Magenta
        }
    }
}

# ========================================
# Step 5: テストスクリプトの確認
# ========================================
Write-Host "`n=== Step 5: テストスクリプトの確認 ===" -ForegroundColor Cyan

$testFiles = Get-ChildItem -Path "." -Filter "test_*.py" -File | Select-Object Name

Write-Host "テストスクリプト一覧:" -ForegroundColor Yellow
$testFiles | ForEach-Object {
    Write-Host "   - $($_.Name)" -ForegroundColor Green
}

# ========================================
# Step 6: 本体責務ファイルの確認
# ========================================
Write-Host "`n=== Step 6: 本体責務の実装ファイル確認 ===" -ForegroundColor Cyan

$coreFiles = @(
    "src/source_adapters/mercari_adapter.py",
    "src/source_adapters/yahoo_adapter.py",
    "src/source_adapters/hardoff_adapter.py",
    "src/ebay_integration/browse_api_client.py",
    "src/research_workflow/product_matcher.py",
    "src/research_workflow/profit_calculator_v2.py",
    "src/research_workflow/csv_handler.py",
    "src/research_workflow/audit_logger.py"
)

Write-Host "本体責務ファイル:" -ForegroundColor Green
foreach ($file in $coreFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        Write-Host "   ✅ $file ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $file (NOT FOUND)" -ForegroundColor Red
    }
}

# ========================================
# Summary
# ========================================
Write-Host "`n=== 🔍 棚卸し完了 ===" -ForegroundColor Cyan
Write-Host "確認内容:" -ForegroundColor Yellow
Write-Host "  1. メール通知関連ファイル" -ForegroundColor Yellow
Write-Host "  2. デプロイスクリプト内の不要な処理" -ForegroundColor Yellow
Write-Host "  3. Pythonコード内の仕様外キーワード" -ForegroundColor Yellow
Write-Host "  4. ドキュメント内の矛盾" -ForegroundColor Yellow
Write-Host "  5. テストスクリプトの一覧" -ForegroundColor Yellow
Write-Host "  6. 本体責務ファイルの確認" -ForegroundColor Yellow
