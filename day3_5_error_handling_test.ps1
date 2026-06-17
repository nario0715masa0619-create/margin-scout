# ============================================================================
# Day 3-5 エラーハンドリング検証 PowerShell スクリプト
# ============================================================================
# 目的: E2E フロー異常系の検証（ネットワークエラー、タイムアウト、不正 job_id）
# 実行: powershell -ExecutionPolicy Bypass -File .\day3_5_error_handling_test.ps1
# ============================================================================

param(
    [string]$Stage = "day3",  # day3, day4, day5
    [string]$ProjectRoot = "C:\NewProjects\margin-scout"
)

# === 初期化 ===
$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = Join-Path $ProjectRoot "test_results"
$docDir = Join-Path $ProjectRoot "docs"
$testDir = Join-Path $ProjectRoot "test_scripts"

# ディレクトリ作成
@($logDir, $docDir, $testDir) | ForEach-Object {
    if (-not (Test-Path $_)) { New-Item -ItemType Directory -Force $_ | Out-Null }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Day 3-5 エラーハンドリング検証スクリプト" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ステージ: $Stage" -ForegroundColor Green
Write-Host "プロジェクト: $ProjectRoot" -ForegroundColor Green
Write-Host ""

# === ファイル生成 1: ERROR_HANDLING_TEST_SCENARIOS.md ===
$scenariosDoc = @"
# エラーハンドリング検証シナリオ (Day 3-5)

## 概要
MarginScout v2.1 の異常系検証を 3 段階で実施。各段階で特定のエラータイプをシミュレートし、UI・ログ・エラーメッセージの挙動を検証。

---

## Day 3: ネットワークエラー検証 (パターン 1)

### シナリオ
1. **準備フェーズ**
   - Backend を完全に停止
   - Frontend: \`http://localhost:5173\` を開く
   - S01 (リサーチ開始) 画面を表示

2. **実行フェーズ**
   - キーワード: "iPhone"
   - ソース: 全選択
   - "リサーチ開始" ボタンをクリック

3. **検証フェーズ**
   - ErrorModal 表示確認: "Connection refused" メッセージが表示されるか
   - LogPanel に \`error\` ログが記録されるか
   - "再試行" ボタンが表示されるか
   - Backend 再起動後、再試行ボタンで正常に続行できるか

### 期待値
\`\`\`
✅ ErrorModal: Connection refused (または Network Error)
✅ LogPanel: [ERROR] POST /api/research/jobs failed: ...
✅ 再試行ボタン: 存在・クリック可能
✅ Backend 再起動後: 再試行で S02 へ正常遷移
\`\`\`

### チェックリスト
- [ ] ErrorModal タイトル正確性
- [ ] エラーメッセージ内容正確性
- [ ] ログレベル (ERROR) 正確性
- [ ] 再試行ボタン動作
- [ ] UI 崩れなし

---

## Day 4: API タイムアウト検証 (パターン 2)

### シナリオ
1. **準備フェーズ**
   - \`margin-scout-backend/app/main.py\` の POST \`/api/research/jobs\` に一時的に以下を追加:
     \`\`\`python
     await asyncio.sleep(35)  # timeout: 30s で強制タイムアウト
     \`\`\`
   - Backend 再起動（注入コード適用）
   - Frontend リロード

2. **実行フェーズ**
   - S01 でリサーチ開始

3. **検証フェーズ**
   - 30 秒後、ErrorModal に "Request Timeout" 表示
   - ステータス: error に更新
   - LogPanel に warning ログ記録
   - 再試行可否

### 期待値
\`\`\`
✅ ErrorModal: Request Timeout
✅ LogPanel: [WARNING] Request timed out after 30s
✅ ステータス表示: error (赤)
✅ 再試行: 可能 (ただし再度タイムアウト)
\`\`\`

### チェックリスト
- [ ] timeout エラーメッセージ
- [ ] ステータス表示更新 (error)
- [ ] ログレベル (WARNING)
- [ ] UI 反応継続 (フリーズなし)
- [ ] **重要**: 検証後、sleep(35) コードを削除して main に戻す

---

## Day 5: 不正 job_id 検証 (パターン 3)

### シナリオ
1. **準備フェーズ**
   - Backend 正常起動
   - Frontend: S01 → S05 フロー完全実行
   - S03 (候補一覧) まで到達

2. **検証フェーズ**
   - ブラウザコンソール (F12) を開く
   - localStorage を確認: \`console.log(localStorage.getItem('job_id'))\`
   - **job_id を不正値に変更**: \`localStorage.setItem('job_id', 'invalid_12345')\`
   - S04 (詳細) ページへナビゲート試行

3. **確認フェーズ**
   - ErrorModal: "Job not found (404)" 表示
   - LogPanel: error ログ記録
   - S03 へ戻せるか確認

### 期待値
\`\`\`
✅ ErrorModal: Job not found
✅ HTTP Status: 404
✅ LogPanel: [ERROR] GET /api/research/jobs/invalid_12345 returned 404
✅ 戻るボタン: S03 に正常遷移
\`\`\`

### チェックリスト
- [ ] 404 エラー検出
- [ ] エラーメッセージ正確性
- [ ] ログ記録
- [ ] 画面遷移正常性
- [ ] **重要**: localStorage を元の job_id に戻す

---

## 全段階共通の検証項目

| 項目 | Day 3 | Day 4 | Day 5 |
|---|---|---|---|
| ErrorModal 表示 | ✅ | ✅ | ✅ |
| LogPanel 記録 | ✅ | ✅ | ✅ |
| エラーメッセージ正確 | ✅ | ✅ | ✅ |
| UI フリーズなし | ✅ | ✅ | ✅ |
| 再試行または復帰 | ✅ | ✅ | ✅ |
| コンソールエラーなし | ✅ | ✅ | ✅ |

---

## 実行順序と期間
- **Day 3** (約 15 分): ネットワークエラー
- **Day 4** (約 20 分): タイムアウト
- **Day 5** (約 10 分): 不正 job_id
- **結果記録**: 各日終了後に \`day_X_report.md\` に記入

---

## 重要: コード修正の注意
- **Day 4 のタイムアウト注入**: 検証終了後、**必ず \`sleep(35)\` コードを削除** してから main ブランチにコミット
- **localStorage 変更**: Day 5 検証終了後、**必ず元の job_id に戻す** またはブラウザキャッシュをクリア

---

## GO/NO-GO 判定
- **GO**: 全パターン 3/3 成功、全チェックリスト ✅、UI 安定性確認
- **NO-GO**: 1 つ以上の失敗、再現不可能なエラー、ドキュメント不一致
"@

$scenariosPath = Join-Path $docDir "ERROR_HANDLING_TEST_SCENARIOS.md"
Set-Content -Path $scenariosPath -Value $scenariosDoc -Encoding UTF8
Write-Host "✅ 生成: ERROR_HANDLING_TEST_SCENARIOS.md" -ForegroundColor Green

---

# === ファイル生成 2: error_injection_helper.py ===
$helperScript = @"
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
TIMEOUT_CODE = ""`"
    # [ERROR_INJECTION_TIMEOUT_START]
    import asyncio
    await asyncio.sleep(35)  # Force timeout (threshold: 30s)
    # [ERROR_INJECTION_TIMEOUT_END]
""`"

def inject_timeout():
    ""`"POST /api/research/jobs に sleep(35) を挿入""`"
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
    ""`"sleep(35) コードを削除""`"
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
"@

$helperPath = Join-Path $testDir "error_injection_helper.py"
Set-Content -Path $helperPath -Value $helperScript -Encoding UTF8
Write-Host "✅ 生成: test_scripts/error_injection_helper.py" -ForegroundColor Green

---

# === ファイル生成 3: レポートテンプレート ===
$reportTemplate = @"
# Day 3-5 エラーハンドリング検証レポート

## 実行日: $timestamp

---

## Day 3: ネットワークエラー検証

### 実行時刻
- 開始: [記入]
- 終了: [記入]
- 所要時間: [記入]

### 実行内容
- Backend 停止状態でリサーチ開始ボタンをクリック
- キーワード: iPhone
- ソース: 全選択

### 検証結果

| 項目 | 期待値 | 実績 | 判定 |
|---|---|---|---|
| ErrorModal 表示 | Connection refused | [記入] | [ ] ✅ / [ ] ❌ |
| エラーメッセージ | 正確 | [記入] | [ ] ✅ / [ ] ❌ |
| LogPanel ログ記録 | error レベル | [記入] | [ ] ✅ / [ ] ❌ |
| 再試行ボタン | 存在・動作 | [記入] | [ ] ✅ / [ ] ❌ |
| Backend 再起動後の復帰 | S02 へ正常遷移 | [記入] | [ ] ✅ / [ ] ❌ |

### チェックリスト
- [ ] ErrorModal タイトル正確性
- [ ] エラーメッセージ内容正確性
- [ ] ログレベル (ERROR) 正確性
- [ ] 再試行ボタン動作
- [ ] UI 崩れなし
- [ ] ブラウザコンソールエラーなし

### 結果判定
- [ ] **PASS** (全項目チェック完了)
- [ ] **FAIL** (失敗項目: [記入])
- [ ] **RETRY** (理由: [記入])

### 備考
[特記事項・スクリーンショット参照番号・ログ URL などを記入]

---

## Day 4: API タイムアウト検証

### 実行時刻
- 開始: [記入]
- 終了: [記入]
- 所要時間: [記入]

### 準備内容
- error_injection_helper.py --inject 実行日時: [記入]
- Backend 再起動: [記入]

### 実行内容
- リサーチ開始ボタンをクリック
- 30 秒待機してタイムアウト確認

### 検証結果

| 項目 | 期待値 | 実績 | 判定 |
|---|---|---|---|
| ErrorModal 表示 | Request Timeout | [記入] | [ ] ✅ / [ ] ❌ |
| ステータス表示 | error (赤) | [記入] | [ ] ✅ / [ ] ❌ |
| LogPanel ログレベル | WARNING | [記入] | [ ] ✅ / [ ] ❌ |
| 再試行可否 | 可能 | [記入] | [ ] ✅ / [ ] ❌ |
| UI フリーズ | なし | [記入] | [ ] ✅ / [ ] ❌ |

### チェックリスト
- [ ] タイムアウトメッセージ
- [ ] ステータス表示更新 (error)
- [ ] ログレベル (WARNING)
- [ ] UI 反応継続
- [ ] コンソールエラーなし
- [ ] **重要**: error_injection_helper.py --revert で復帰確認: [記入]

### 結果判定
- [ ] **PASS** (全項目チェック + 復帰確認)
- [ ] **FAIL** (失敗項目: [記入])
- [ ] **RETRY** (理由: [記入])

### 備考
[特記事項・復帰時刻・検証内容など記入]

---

## Day 5: 不正 job_id 検証

### 実行時刻
- 開始: [記入]
- 終了: [記入]
- 所要時間: [記入]

### 準備内容
- S01 → S05 フロー完全実行完了時刻: [記入]
- localStorage 変更: job_id → invalid_12345

### 実行内容
- S04 詳細ページへのナビゲート試行
- ブラウザコンソール F12 で確認

### 検証結果

| 項目 | 期待値 | 実績 | 判定 |
|---|---|---|---|
| ErrorModal 表示 | Job not found (404) | [記入] | [ ] ✅ / [ ] ❌ |
| HTTP Status | 404 | [記入] | [ ] ✅ / [ ] ❌ |
| LogPanel ログレベル | ERROR | [記入] | [ ] ✅ / [ ] ❌ |
| 戻るボタン動作 | S03 へ正常遷移 | [記入] | [ ] ✅ / [ ] ❌ |
| localStorage 復帰 | 元の job_id に戻す | [記入] | [ ] ✅ / [ ] ❌ |

### チェックリスト
- [ ] 404 エラー検出
- [ ] エラーメッセージ正確性
- [ ] ログ記録
- [ ] 画面遷移正常性
- [ ] localStorage クリア・復帰
- [ ] コンソールエラーなし

### 結果判定
- [ ] **PASS** (全項目チェック + localStorage 復帰)
- [ ] **FAIL** (失敗項目: [記入])
- [ ] **RETRY** (理由: [記入])

### 備考
[特記事項・localStorage 値・検証内容など記入]

---

## 全体判定

### 段階別結果
- Day 3: [ ] PASS / [ ] FAIL / [ ] RETRY
- Day 4: [ ] PASS / [ ] FAIL / [ ] RETRY
- Day 5: [ ] PASS / [ ] FAIL / [ ] RETRY

### 最終判定
- [ ] **GO** (全段階 PASS、異常系対応確認完了)
- [ ] **NO-GO** (失敗段階: [記入]、要修正)
- [ ] **条件付き GO** (軽微な問題のみ: [記入])

### 承認
- レポート作成者: [記入]
- 作成日時: $timestamp
- 確認者: [記入]
- 確認日時: [記入]

---

## 添付資料
- スクリーンショット: [ファイル名]
- ブラウザコンソール出力: [記入]
- Backend ログ: [記入]
- その他: [記入]
"@

$reportPath = Join-Path $logDir "error_handling_report_template.md"
Set-Content -Path $reportPath -Value $reportTemplate -Encoding UTF8
Write-Host "✅ 生成: test_results/error_handling_report_template.md" -ForegroundColor Green

---

# === ステージ別実行ガイド表示 ===
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Day 3-5 検証ガイド" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$dayGuide = @{
    "day3" = @"
🔴 **Day 3: ネットワークエラー検証**

【準備】
1. Backend を停止:
   Ctrl+C で Backend ターミナルを終了
   
2. Frontend は実行中のまま: \`http://localhost:5173\`

【実行】
1. S01 (リサーチ開始) 画面を表示
2. キーワード: "iPhone"
3. ソース: 全選択
4. "リサーチ開始" ボタンをクリック

【検証】
✓ ErrorModal: "Connection refused" メッセージ表示
✓ LogPanel: error ログ記録
✓ "再試行" ボタン存在・動作
✓ Backend 再起動後、再試行で正常続行

【結果記録】
→ $reportPath
  Day 3 セクションに結果を記入してください
"@;
    "day4" = @"
⏱️  **Day 4: API タイムアウト検証**

【準備】
1. Backend を停止

2. error_injection_helper.py でタイムアウト注入:
   cd $ProjectRoot
   python $testDir/error_injection_helper.py --inject

3. Backend 再起動:
   cd margin-scout-backend
   .\venv_backend\Scripts\activate
   python -m uvicorn app.main:app --reload

4. Frontend リロード

【実行】
1. S01 (リサーチ開始) 画面を表示
2. "リサーチ開始" ボタンをクリック
3. 30 秒待機

【検証】
✓ ErrorModal: "Request Timeout" メッセージ表示
✓ ステータス: error (赤色)
✓ LogPanel: WARNING ログレベル
✓ UI フリーズなし

【重要: 検証終了後】
python $testDir/error_injection_helper.py --revert
Backend 再起動: python -m uvicorn app.main:app --reload

【結果記録】
→ $reportPath
  Day 4 セクションに結果・復帰時刻を記入
"@;
    "day5" = @"
🆔  **Day 5: 不正 job_id 検証**

【準備】
1. Backend: 正常起動状態 ✓

2. S01 → S05 フロー完全実行
   - リサーチ開始
   - 完了まで待機
   - 候補一覧表示確認

【実行】
1. ブラウザ F12 でコンソール開く

2. localStorage 確認:
   console.log(localStorage.getItem('job_id'))
   
3. job_id を不正値に変更:
   localStorage.setItem('job_id', 'invalid_12345')

4. S04 (詳細) ページへナビゲート試行

【検証】
✓ ErrorModal: "Job not found (404)"
✓ HTTP Status: 404 確認
✓ LogPanel: ERROR ログレベル
✓ "戻る" ボタン: S03 へ正常遷移
✓ localStorage を元の job_id に復帰

【結果記録】
→ $reportPath
  Day 5 セクションに結果・localStorage 値を記入
"@
}

Write-Host ""
Write-Host $dayGuide[$Stage] -ForegroundColor Yellow
Write-Host ""

Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ スクリプト生成完了" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📁 生成ファイル:" -ForegroundColor Cyan
Write-Host "  1. $scenariosPath" -ForegroundColor White
Write-Host "  2. $helperPath" -ForegroundColor White
Write-Host "  3. $reportPath" -ForegroundColor White
Write-Host ""
Write-Host "📋 次のステップ:" -ForegroundColor Cyan
Write-Host "  1. docs/ERROR_HANDLING_TEST_SCENARIOS.md を確認" -ForegroundColor White
Write-Host "  2. 上記の Day $($Stage.ToUpper()) ガイドに従い実行" -ForegroundColor White
Write-Host "  3. 結果を レポートテンプレート に記入" -ForegroundColor White
Write-Host "  4. 次の段階へ進行" -ForegroundColor White
Write-Host ""
Write-Host "🚀 Day $($Stage.ToUpper()) 検証を開始してください！" -ForegroundColor Green
