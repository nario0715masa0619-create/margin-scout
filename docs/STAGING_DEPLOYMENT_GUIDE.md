# 📋 MarginScout v2.1 ステージング環境運用ガイド

**バージョン**: 1.0  
**ステータス**: Staging Deployment  
**期間**: 1～2 週間  
**目標**: 本番環境への安定稼働確認

---

## 🎯 ステージング運用の目的

| 項目 | 目標 | 確認方法 |
|------|------|--------|
| **安定性** | 致命的障害ゼロ | ログ監視 |
| **UI/API 動線** | E2E フロー安定 | 手動テスト + ログ確認 |
| **CSV 出力** | 毎回成功 | ダウンロード検証 |
| **ログ追跡** | 失敗原因特定可能 | ログパネル + 詳細分析 |
| **Live API** | eBay API 安定接続 | ポーリング成功率 |
| **ドキュメント** | 実装と一致 | マニュアル確認 |

---

## 📦 ステージング環境構築

### **Option A: Docker Compose（推奨）**

#### **docker-compose.yml**

```yaml
version: '3.8'

services:
  # Backend FastAPI
  backend:
    build: ./margin-scout-backend
    ports:
      - "8000:8000"
    environment:
      - EBAY_ENV=live
      - EBAY_CLIENT_ID=${EBAY_CLIENT_ID}
      - EBAY_CLIENT_SECRET=${EBAY_CLIENT_SECRET}
      - EXCHANGE_RATE_JPY=157.50
      - LOG_LEVEL=info
    volumes:
      - ./margin-scout-backend:/app
    command: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Frontend Vue
  frontend:
    build: ./margin-scout-ui
    ports:
      - "5173:5173"
    volumes:
      - ./margin-scout-ui:/app
      - /app/node_modules
    environment:
      - VITE_API_BASE_URL=http://backend:8000/api
    command: npm run dev
    depends_on:
      - backend

  # Nginx リバースプロキシ（本番テスト用）
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
```

#### 起動手順

```bash
# .env ファイル作成
cat > .env << EOF
EBAY_CLIENT_ID=your-staging-client-id
EBAY_CLIENT_SECRET=your-staging-secret
EOF

# Docker Compose 起動
docker-compose up -d

# ログ確認
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Option B: ローカル起動（開発環境と同じ）

```bash
# ターミナル 1: Backend
cd margin-scout-backend
.\venv_backend\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000

# ターミナル 2: Frontend
cd margin-scout-ui
npm run dev

# ターミナル 3: ログ監視（オプション）
tail -f logs/*.log
```

---

## 📋 ステージング実運用テスト計画

### Week 1: 基本機能検証

#### Day 1-2: 単一フロー検証

【テスト シナリオ A】
目標: S01 → S05 の完全フロー × 5 回実行

手順:
1. http://localhost:5173 にアクセス
2. キーワード: "iPhone, Canon" を入力
3. ソース: すべて選択
4. 「リサーチ開始」クリック
5. S02 で進捗を確認（2秒間隔ポーリング）
6. 完了後 S03 で候補を確認
7. 3～5 件選択
8. S05 で CSV ダウンロード
9. CSV 内容確認
10. ブラウザ開発者ツール → Console でエラー確認

#### Day 3-5: エラー処理検証

【テスト シナリオ B】
目標: エラーハンドリング動作確認

1️⃣ ネットワークエラーシミュレーション
2️⃣ API タイムアウトテスト
3️⃣ 不正な job_id アクセス

### Week 2: 安定性 + 連続実行テスト

#### Day 6-8: 連続実行 + ポーリング安定性

【テスト シナリオ C】
目標: 連続実行時の安定性 + Job 管理
1. S01 から 10 回連続でリサーチ開始

#### Day 9-10: eBay Live API 安定性

【テスト シナリオ D】
目標: eBay Browse API への実接続安定性確認
1. 複数キーワード で eBay API 呼び出し確認

### Week 2: ドキュメント + 本番移行判定

#### Day 11-12: ドキュメント検証 + 最終確認

【チェックリスト】
- [x] README.md と実装が一致しているか
- [x] 本番移行判定条件クリア

---

## 🔍 監視・ログ管理

### ログパネル活用
1. LogPanel を毎日確認
2. エラー内容を記録

---

## ✅ 本番移行 GO/NO-GO 判定基準

### GO 条件（全て満たす）
- ステージング 1～2 週間で致命的障害なし
- E2E フロー 30 回以上連続成功（成功率 100%）
- エラーハンドリング全パターン正常動作
- ログパネルから全失敗原因追跡可能
- eBay API 応答時間 < 1000ms（99%）
- ドキュメント実装と 100% 一致
- CSV 出力成功率 100%

### NO-GO 条件（1つでも満たす）
- 致命的障害（システムクラッシュ）発生
- エラーハンドリング不備で UI 崩壊
- CSV 出力エラー率 > 5%
