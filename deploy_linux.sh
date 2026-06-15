#!/bin/bash
# MarginScout v2.0 - Linux/macOS Cron Launcher

cd /opt/margin-scout || exit 1

# 仮想環境有効化
source venv/bin/activate

# リサーチ実行
python test_operational_multicat_nonmock.py

# ログ出力
echo "[$(date)] Research completed" >> logs/deploy.log

