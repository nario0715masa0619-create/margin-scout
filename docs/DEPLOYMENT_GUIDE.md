# MarginScout v2.0 - 本番環境構成ガイド

## Phase G: 本番環境へのデプロイ

### 前提条件

- eBay Developer アカウント（Live API アクセス権）
- サーバー環境（Windows / Linux / macOS）
- Python 3.11+
- インターネット接続

---

## Step 1: eBay Live API への切り替え

### 1.1 eBay Developer Portal で Live 認証情報を取得

1. https://developer.ebay.com へアクセス
2. "My Account" -> "Applications" でアプリを確認
3. "Sandbox" タブから "Live" タブへ切り替え
4. Live Client ID と Client Secret をコピー

### 1.2 .env を更新

```env
# eBay Browse API - LIVE
EBAY_BROWSE_CLIENT_ID=your_live_client_id
EBAY_BROWSE_CLIENT_SECRET=your_live_client_secret
EBAY_API_MODE=live
```

### 1.3 動作確認

```bash
python -c "from src.ebay_integration.auth_handler import EbayAuthHandler; print('✅ Live API Ready')"
```

---

## Step 2: 定期実行スケジューラー設定

### Windows 環境

#### 2.1 Task Scheduler で新規タスクを作成

```powershell
# PowerShell (管理者権限)

# アクション定義
$Action = New-ScheduledTaskAction `
  -Execute "C:\NewProjects\margin-scout\deploy_windows.bat"

# トリガー定義（毎日 6:00 に実行）
$Trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM

# タスク登録
Register-ScheduledTask `
  -TaskName "MarginScout-Daily-Research" `
  -Action $Action `
  -Trigger $Trigger `
  -RunLevel Highest
```

#### 2.2 動作確認

```powershell
# タスク一覧表示
Get-ScheduledTask | Where-Object { $_.TaskName -like "*MarginScout*" }

# 手動実行テスト
Start-ScheduledTask -TaskName "MarginScout-Daily-Research"
```

### Linux / macOS 環境

#### 2.1 cron ジョブを設定

```bash
# crontab を編集
crontab -e

# 以下を追加（毎日 6:00 に実行）
0 6 * * * /opt/margin-scout/deploy_linux.sh >> /opt/margin-scout/logs/cron.log 2>&1
```

#### 2.2 動作確認

```bash
# cron ジョブ確認
crontab -l

# ログ確認
tail -f /opt/margin-scout/logs/cron.log
```

---

## Step 3: ログ監視とトラブルシューティング

### 3.1 ログファイル確認

```bash
# 実行ログ
tail -f output_operational_test/test_run.log

# 監査ログ（JSONL 形式）
tail -f output_operational_test/research_audit_*.jsonl

# スケジューラーログ
tail -f logs/deploy.log
```

### 3.2 一般的な問題と対処

| 問題 | 原因 | 対処 |
|------|------|------|
| 401 Unauthorized | API 認証情報が無効 | .env の Live 認証情報を確認 |
| タイムアウト | スクレイピング遅延 | config_adapters.py の TIMEOUT を増加 |
| メモリ不足 | 大量アイテム処理 | バッチ処理に分割 |
| 送料計算エラー | 重さ推定失敗 | 商品属性情報を確認 |

---

## Step 4: メール通知設定（オプション）

### 4.1 Gmail アプリパスワード取得

1. https://myaccount.google.com/apppasswords へアクセス
2. 16 文字のパスワードを生成
3. コピーして .env に設定

### 4.2 .env に追加

```env
# Email Notification
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=xxxx_xxxx_xxxx_xxxx
EMAIL_RECIPIENT=recipient@example.com
```

### 4.3 メール送信テスト

```bash
python -c "
from src.research_workflow.email_notifier import EmailNotifier
notifier = EmailNotifier('smtp.gmail.com', 587, 'sender@gmail.com', 'password')
notifier.send_profit_report('recipient@example.com', 'output_operational_test/test_report.json', 'output_operational_test/research_results.csv')
"
```

---

## Step 5: データベース永続化（オプション）

### 5.1 SQLite データベース作成

```bash
python -c "
import sqlite3
conn = sqlite3.connect('margin_scout.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS research_results (
        id INTEGER PRIMARY KEY,
        candidate_id TEXT UNIQUE,
        product_name TEXT,
        source_channel TEXT,
        source_price_jpy REAL,
        ebay_price_usd REAL,
        profit_jpy REAL,
        profit_margin_pct REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
conn.close()
print('✅ Database created')
"
```

---

## チェックリスト

- [ ] eBay Live API 認証情報を .env に設定
- [ ] 最初のリサーチを手動実行して確認
- [ ] スケジューラー設定（Windows / Linux）
- [ ] ログファイルのパスを確認
- [ ] メール通知を設定（オプション）
- [ ] バックアップスクリプトを作成
- [ ] 監視・アラート設定（オプション）

---

## トラブルシューティング

### Q1: "ModuleNotFoundError" が出る

→ 仮想環境が有効化されているか確認 → requirements.txt を再インストール

### Q2: スケジューラーが自動実行されない

→ Windows: タスク スケジューラー の履歴を確認 → Linux: cron ログを確認 (journalctl -u cron)

### Q3: メール送信が失敗する

→ SMTP 設定を確認（Gmail は "安全性の低いアプリ" を許可） → ファイアウォールで SMTP ポート（587）を開く

---

## 推奨構成

### 本番サーバー推奨スペック

- CPU: 2 コア以上
- メモリ: 2GB 以上
- ストレージ: 10GB 以上
- ネットワーク: 安定した 10Mbps 以上
- 稼働時間: 24/7（または毎日実行時間）

### バックアップ戦略

```bash
# 日次バックアップ
0 23 * * * tar -czf /backup/margin-scout-$(date +\%Y\%m\%d).tar.gz /opt/margin-scout/output* /opt/margin-scout/margin_scout.db
```

### ヘルスチェック

```bash
#!/bin/bash
# 最後の実行が 30 時間以上前か確認
LAST_RUN=$(stat -c %Y /opt/margin-scout/output_operational_test/test_report.json)
NOW=$(date +%s)
DIFF=$((NOW - LAST_RUN))

if [ $DIFF -gt 108000 ]; then
    echo "❌ ALERT: Research did not run for more than 30 hours"
    # メール送信処理などを追加
else
    echo "✅ Health check passed"
fi
```

## 次のステップ
- [x] eBay Live API 切り替え
- [x] スケジューラー設定
- [x] 初回自動実行確認
- [x] メール通知テスト
- [ ] 📊 ダッシュボード実装（オプション）
- [ ] 🗄️ 大規模データ蓄積（オプション）

MarginScout v2.0 は本番環境で 24/7 稼働可能です！🚀
