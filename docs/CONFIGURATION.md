# MarginScout Configuration Guide

## 正式な .env 配置場所

**推奨（デフォルト）:**
```
C:\Users\{username}\.marginscount\.env
```

**フォールバック:**
```
{project_root}\.env
```

## Phase 6: eBay OAuth & Live API 設定

### 統一された環境変数キー

MarginScout は以下の **公式環境変数キー** を使用します：

| 変数名 | 説明 | 必須 | 例 |
|--------|------|------|-----|
| EBAY_ENV | 環境（sandbox/production） | No | sandbox |
| EBAY_CLIENT_ID | eBay App ID | Yes | AppId_123456 |
| EBAY_CLIENT_SECRET | eBay Cert ID | Yes | CertId_abcdef |
| EBAY_REDIRECT_URI | OAuth redirect URI | No | http://localhost:8080/callback |
| EBAY_REFRESH_TOKEN | eBay refresh token | No* | v^1.1#i^1#... |
| EBAY_REQUEST_TIMEOUT | API request timeout秒 | No | 30 |
| EBAY_MAX_RETRIES | API retry回数 | No | 3 |

*EBAY_REFRESH_TOKEN は Phase 6 live API 呼び出し時に必須です。

### .env ファイル作成手順

1. **ホームディレクトリに .marginscount フォルダを作成:**
```bash
mkdir -p ~/.marginscount
```

2. **.env ファイルを作成:**
```bash
cat > ~/.marginscount/.env << EOF
EBAY_ENV=sandbox
EBAY_CLIENT_ID=your_app_id_here
EBAY_CLIENT_SECRET=your_cert_id_here
EBAY_REDIRECT_URI=http://localhost:8080/callback
EBAY_REFRESH_TOKEN=
EBAY_REQUEST_TIMEOUT=30
EBAY_MAX_RETRIES=3
EOF
```

3. **パーミッション設定（Unix/Linux/Mac）:**
```bash
chmod 600 ~/.marginscount/.env
```

### 後方互換性

以下の旧キー名も読込可能です（非推奨）：
- EBAY_SANDBOX_CLIENT_ID → EBAY_CLIENT_ID に統合
- EBAY_SANDBOX_CLIENT_SECRET → EBAY_CLIENT_SECRET に統合
- EBAY_APP_ID → EBAY_CLIENT_ID に統合

新規プロジェクトは公式キー名を使用してください。

### 設定確認

```bash
python -m src.config_loader
```

出力例:
```json
{
  "env_file_path": "C:\\Users\\username\\.marginscount\\.env",
  "ebay_env": "sandbox",
  "ebay_client_id": "AppId_123...",
  "ebay_client_secret": "***masked***",
  "ebay_redirect_uri": "http://localhost:8080/callback",
  "ebay_refresh_token": "***masked***"
}
```

## Sandbox Connection Test

```bash
python sandbox_connection_test.py
```

テスト項目:
1. Configuration Loading
2. OAuth Handler Initialization
3. API Client Initialization
4. Token Configuration Check
