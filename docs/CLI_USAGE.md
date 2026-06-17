# CLI Usage (MarginScout v2.1)

## 推奨: UI から実行（Web ブラウザ）

```bash
cd margin-scout-ui
npm run dev
# http://localhost:5173 で操作
```

## 補助: CLI から直接実行

```bash
python cli.py --input-csv <INPUT_CSV> --output-dir <OUTPUT_DIR>

# 例：
python cli.py --input-csv samples/candidates.csv --output-dir ./output
```

## オプション
- `--input-csv`: 入力 CSV ファイルパス（必須）
- `--output-dir`: 出力ディレクトリ（デフォルト: ./output_operational_test）

## 出力ファイル
- research_results.csv: 利益候補一覧
- research_summary.json: 実行サマリー
- logs/research_audit_*.jsonl: 監査ログ
