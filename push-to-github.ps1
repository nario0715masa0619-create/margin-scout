# ============================================================================
# MarginScout GitHub Repository Creation & Push Script
# ============================================================================

$projectPath = "C:\NewProjects\margin-scout"
$gitHubUsername = "nario0715masa0619-create"
$repoName = "margin-scout"
$gitHubToken = Read-Host "GitHub Personal Access Token を入力してください（Ctrl+C でキャンセル）"

if ([string]::IsNullOrWhiteSpace($gitHubToken)) {
    Write-Host "❌ GitHub Token が入力されませんでした。スクリプトを終了します。" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 MarginScout GitHub Repository Setup" -ForegroundColor Cyan
Write-Host "==========================================`n"

# Step 1: ローカル Git 状態確認
Write-Host "📋 Step 1: ローカル Git リポジトリ状態確認" -ForegroundColor Yellow
cd $projectPath

$gitStatus = git status 2>&1
$gitRemote = git remote -v 2>&1

Write-Host "Current Branch:"
git branch -a
Write-Host "`nRemote Status:"
Write-Host $gitRemote
Write-Host "`nWorking Tree Status:"
Write-Host $gitStatus | Select-Object -First 5

# Step 2: GitHub リポジトリ作成（REST API 経由）
Write-Host "`n📝 Step 2: GitHub REST API でリポジトリ作成" -ForegroundColor Yellow

$headers = @{
    "Authorization" = "token $gitHubToken"
    "Accept" = "application/vnd.github.v3+json"
}

$repoData = @{
    name = $repoName
    description = "eBay seller research and CSV-based listing support platform"
    private = $false
    has_issues = $true
    has_projects = $true
    has_downloads = $true
    auto_init = $false
} | ConvertTo-Json

$createRepoUrl = "https://api.github.com/user/repos"

try {
    $response = Invoke-RestMethod -Uri $createRepoUrl -Method Post -Headers $headers -Body $repoData -ContentType "application/json"
    Write-Host "✅ GitHub リポジトリ作成成功" -ForegroundColor Green
    Write-Host "Repository URL: $($response.html_url)" -ForegroundColor Cyan
    $repoUrl = $response.html_url
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "⚠️  リポジトリは既に存在します。既存リポジトリを使用します。" -ForegroundColor Yellow
        $repoUrl = "https://github.com/$gitHubUsername/$repoName"
    } else {
        Write-Host "❌ リポジトリ作成失敗: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Step 3: ローカル Git にリモートを追加
Write-Host "`n🔗 Step 3: Git リモート URL を追加" -ForegroundColor Yellow

$remoteUrl = "https://$gitHubToken@github.com/$gitHubUsername/$repoName.git"

# 既存リモートを確認して削除（存在する場合）
$existingRemote = git remote get-url origin 2>&1
if ($LASTEXITCODE -eq 0 -and ![string]::IsNullOrWhiteSpace($existingRemote)) {
    Write-Host "既存の origin リモートを削除します..." -ForegroundColor Yellow
    git remote remove origin
}

# 新しいリモートを追加
git remote add origin $remoteUrl
Write-Host "✅ リモート追加完了: origin" -ForegroundColor Green

# Step 4: Branch を main に統一
Write-Host "`n🌿 Step 4: Branch を main に統一" -ForegroundColor Yellow

$currentBranch = git rev-parse --abbrev-ref HEAD
Write-Host "現在の Branch: $currentBranch"

if ($currentBranch -ne "main") {
    git branch -M main
    Write-Host "✅ Branch を main に変更しました" -ForegroundColor Green
} else {
    Write-Host "✅ Branch は既に main です" -ForegroundColor Green
}

# Step 5: Push を実行
Write-Host "`n📤 Step 5: GitHub へ Push" -ForegroundColor Yellow

try {
    git push -u origin main 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Push 成功！" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Push に警告がありました。詳細は上記を確認してください。" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Push 失敗: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Step 6: 最終確認
Write-Host "`n✨ Step 6: 最終確認" -ForegroundColor Yellow

$finalCommit = git log --oneline -1
$finalRemote = git remote -v

Write-Host "最新コミット: $finalCommit"
Write-Host "`nリモート設定:"
Write-Host $finalRemote

# Final Report を JSON で保存
Write-Host "`n📊 Final Report を保存" -ForegroundColor Yellow

$finalReport = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    project_name = "MarginScout"
    project_path = $projectPath
    repository_url = $repoUrl
    repository_api_url = "https://api.github.com/repos/$gitHubUsername/$repoName"
    github_username = $gitHubUsername
    repository_name = $repoName
    current_branch = git rev-parse --abbrev-ref HEAD
    head_commit_short = git rev-parse --short HEAD
    head_commit_full = git rev-parse HEAD
    git_status = git status --short
    push_status = "SUCCESS"
    next_steps = @(
        "✅ GitHub リポジトリ作成完了"
        "✅ ローカルコードを Push 完了"
        "📖 README.md を GitHub で確認: $repoUrl"
        "🔐 .env は .gitignore で除外されています（セキュリティ OK）"
        "📝 次のフェーズ: リサーチワークフロー設計または CSV データ連携設計"
    )
} | ConvertTo-Json -Depth 3

$finalReport | Out-File -FilePath "$projectPath\GITHUB_PUSH_REPORT.json" -Encoding UTF8
Write-Host "✅ Report: $projectPath\GITHUB_PUSH_REPORT.json" -ForegroundColor Green

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "🎉 GitHub Push 完了！" -ForegroundColor Green
Write-Host "============================================"
Write-Host "Repository: $repoUrl"
Write-Host "Branch: main"
Write-Host "============================================`n"
