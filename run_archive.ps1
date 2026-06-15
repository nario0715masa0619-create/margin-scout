cd C:\NewProjects\margin-scout

# ========================================
# Step 1: archive ディレクトリ作成
# ========================================
Write-Host "=== Step 1: アーカイブディレクトリ作成 ===" -ForegroundColor Cyan
if (-not (Test-Path "docs/archive")) {
    New-Item -ItemType Directory -Path "docs/archive" -Force | Out-Null
    Write-Host "✅ docs/archive/ 作成完了" -ForegroundColor Green
}

# ========================================
# Step 2: 過去の経緯ドキュメントを移動
# ========================================
Write-Host "`n=== Step 2: 過去のドキュメントを archive へ移動 ===" -ForegroundColor Cyan

$archiveTargets = @(
    "PROJECT_FINAL_REPORT.md",
    "PHASE_ABC_IMPLEMENTATION_REPORT.md",
    "PHASE_D_IMPLEMENTATION_REPORT.md",
    "PHASE_D0_SOURCE_ADAPTER_MIGRATION_REPORT.md",
    "MARGINSCOUT_PROJECT_COMPLETION_SUMMARY.md",
    "FINAL_MARGINSCOUT_VERIFICATION_REPORT.md",
    "README_LISTING_APP_INITIAL_SUMMARY.md"
)

foreach ($doc in $archiveTargets) {
    if (Test-Path $doc) {
        Move-Item -Path $doc -Destination "docs/archive/" -Force
        Write-Host "✅ $doc → docs/archive/" -ForegroundColor Green
    } elseif (Test-Path "docs/$doc") {
        Move-Item -Path "docs/$doc" -Destination "docs/archive/" -Force
        Write-Host "✅ docs/$doc → docs/archive/" -ForegroundColor Green
    }
}

# ========================================
# Step 3: 仕様準拠ドキュメント一覧確認
# ========================================
Write-Host "`n=== Step 3: 仕様準拠ドキュメント確認 ===" -ForegroundColor Cyan

$specCompliantDocs = @(
    "README.md",
    "docs/MARGINSCOUT_REDEFINED.md",
    "docs/MARGINSCOUT_SCOPE.md",
    "docs/API_SCOPE_DEFINITION.md",
    "docs/DEPLOYMENT_GUIDE.md"
)

Write-Host "✅ 仕様準拠ドキュメント:" -ForegroundColor Green
foreach ($doc in $specCompliantDocs) {
    if (Test-Path $doc) {
        $size = (Get-Item $doc).Length
        Write-Host "   ✅ $doc ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $doc (NOT FOUND)" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ アーカイブ作成確認:" -ForegroundColor Green
if (Test-Path "docs/archive") {
    $archiveCount = (Get-ChildItem -Path "docs/archive" -File).Count
    Write-Host "   📦 docs/archive/ に $archiveCount 件のドキュメント" -ForegroundColor Green
}

# ========================================
# Step 4: Git コミット準備
# ========================================
Write-Host "`n=== Step 4: Git コミット準備 ===" -ForegroundColor Cyan

Write-Host "`n📝 Git status:" -ForegroundColor Yellow
git status --short
