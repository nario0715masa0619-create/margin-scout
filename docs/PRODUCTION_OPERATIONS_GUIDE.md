# MarginScout v2.1 本番運用ガイド

## 📖 概要
MarginScout v2.1 は、eBay をターゲット市場とした **リサーチ専用ツール** です。

- **責務**: 商品候補取得 → eBay 参考価格照合 → 利益計算 → CSV 出力
- **非責務**: 定期配信、出品実行、在庫管理、注文管理

## 🎯 運用フロー
```text
1. 初期設定（初回のみ）
   ↓
2. 単発実行（手動 or スケジューラ経由）
   ↓
3. 出力確認（CSV/JSON/JSONL）
   ↓
4. 結果分析（利益率、商品品質）
   ↓
5. 定期繰り返し
```

## ⚙️ 初期設定

### Step 1: 環境変数設定
```env
# ~/.marginscount/.env
EBAY_ENV=live
EBAY_CLIENT_ID=your_production_client_id
EBAY_CLIENT_SECRET=your_production_client_secret
EXCHANGE_RATE_JPY=157.50
EBAY_REQUEST_TIMEOUT=30
EBAY_MAX_RETRIES=3
```

### Step 2: Python 依存パッケージ確認
```bash
pip install -r requirements.txt
```

### Step 3: 初回実行テスト
```bash
python cli.py --category electronics --days 90 --min-sales 2
```

## 🚀 本番実行

### 単発実行（推奨）
```bash
python cli.py \
  --category electronics \
  --days 90 \
  --min-sales 2 \
  --output-dir output/
```

### 定期実行設定（オプション）
#### Windows (Task Scheduler)
```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" `
  -Argument "C:\margin-scout\cli.py --category electronics --days 90 --min-sales 2"
$trigger = New-ScheduledTaskTrigger -Daily -At 06:00
Register-ScheduledTask -TaskName "MarginScout Daily" -Action $action -Trigger $trigger -RunLevel Highest
```

#### Linux/macOS (cron)
```bash
# crontab -e
0 6 * * * cd /opt/margin-scout && python cli.py --category electronics --days 90 --min-sales 2 >> logs/cron.log 2>&1
```

## 📊 出力ファイル確認

### CSV 形式 (research_results.csv)
```bash
# 先頭 5 行表示
head -5 output/research_results.csv

# 行数確認
wc -l output/research_results.csv

# 利益額の統計
awk -F, '{sum+=$10} END {print "総利益: " sum}' output/research_results.csv
```

### JSON サマリー (research_summary.json)
```bash
python -m json.tool output/research_summary.json
```

### 監査ログ (research_audit_*.jsonl)
```bash
# 最新ログ確認
tail -20 logs/research_audit_*.jsonl
```

## 🔍 結果分析

### 成功率確認
```bash
# CSV の件数確認
wc -l output/research_results.csv

# 期待値: 52 アイテム入力時に 10～15 件
```

### 利益率分析
```bash
# 平均利益率
awk -F, 'NR>1 {sum+=$11; count++} END {print "平均: " sum/count "%"}' output/research_results.csv

# 黒字件数
awk -F, 'NR>1 && $10>0 {count++} END {print "黒字: " count " 件"}' output/research_results.csv
```

### マッチング精度確認
```bash
# match_score の分布
awk -F, 'NR>1 {print $12}' output/research_results.csv | sort -n
```

## ⚠️ よくあるトラブル

### Q1: 何も出力されない（CSV が空）
**A: 以下を確認**
1. eBay API が正常か（401 エラーがないか）
2. キーワードが eBay に存在するか
3. `match_score < 0.35` で除外されていないか
→ `logs/research_audit_*.jsonl` を確認

### Q2: 利益率がすべて負
**A: 以下を確認**
1. 仕入れ元と eBay の価格差
2. 為替レート設定（`EXCHANGE_RATE_JPY`）
3. eBay 手数料計算ロジック
→ 1～2 件を手動計算で検証

### Q3: eBay API でタイムアウト
**A: 以下を対策**
1. `EBAY_REQUEST_TIMEOUT` を増加（30 → 60）
2. `EBAY_MAX_RETRIES` を確認（3 回まで自動再試行）
3. ネットワーク接続確認

## 📈 KPI トラッキング

### 週次チェック
- [ ] 実行回数: _____ 回
- [ ] 総候補数: _____ 件
- [ ] CSV 出力数: _____ 件
- [ ] 成功率: ______ %
- [ ] 平均利益率: ______ %

### 月次レビュー
- [ ] 成功率推移
- [ ] 利益率推移
- [ ] カテゴリ別成功率
- [ ] マッチング精度

## 🔄 メンテナンス

### 定期確認項目
- [ ] eBay Live API クレデンシャル有効期限
- [ ] 為替レート更新（`EXCHANGE_RATE_JPY`）
- [ ] ログディレクトリサイズ確認
- [ ] エラーログ確認

### ログローテーション（推奨）
```bash
# logs/ ディレクトリを月ごとにアーカイブ
tar -czf logs_backup_2026-06.tar.gz logs/
rm -rf logs/*.jsonl logs/*.log
```

## 🎓 よくある質問

**Q: スケジューラ設定は必須ですか？**
A: いいえ。MarginScout はリサーチ専用ツールで、定期実行は必須ではありません。 ユーザが必要に応じて手動実行、または外部スケジューラ（cron/Task Scheduler）から呼び出してください。

**Q: Sell API（出品）に対応していますか？**
A: いいえ。MarginScout は Browse API（閲覧用）のみで、出品機能はありません。

**Q: Live API から Sandbox に戻せますか？**
A: はい。`EBAY_ENV=sandbox` に変更すれば、Sandbox モードで実行できます。

**Q: CSV 以外のフォーマットに対応していますか？**
A: 現在は CSV のみ。JSON/JSONL は監査ログとして出力しています。

## 📞 サポート
エラー発生時は以下を確認してください：
- `logs/error_*.log` を確認
- `logs/research_audit_*.jsonl` で詳細を確認
- `README.md` のトラブルシューティングを参照
- `DEPLOYMENT_GUIDE.md` で環境設定を確認

**最終更新**: 2026-06-15 **バージョン**: v2.1.0 **ステータス**: Production Ready
