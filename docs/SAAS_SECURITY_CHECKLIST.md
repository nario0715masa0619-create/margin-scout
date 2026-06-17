# MarginScout SaaS - セキュリティチェックリスト

**バージョン**: 1.0  
**作成日**: 2026-06-16

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. 認証・認可セキュリティ

### 1.1 Password セキュリティ

- [x] bcrypt Cost factor 12 以上
- [x] 最小8文字、複雑性チェック
- [x] 平文での保存・通信絶対禁止
- [x] Password リセットメール有効期限 24時間
- [x] ブルートフォース攻撃対策（失敗5回で一時ロック）

### 1.2 JWT トークンセキュリティ

- [x] Secret Key: 最小32文字、ランダム生成
- [x] 署名アルゴリズム: HS256 or RS256（RS256 推奨）
- [x] 有効期限: 24時間（短い方が安全）
- [x] Refresh Token: 別途管理（有効期限 7日）
- [x] Token 破棄: ログアウト時に無効化

### 1.3 セッション管理

- [x] HttpOnly Cookie に token 保存（XSS 対策）
- [x] または Secure flag + SameSite=Strict
- [x] CSRF トークン実装
- [x] セッションタイムアウト: 30分無操作で再認証

---

## 2. API セキュリティ

### 2.1 CORS 設定

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://margin-scout.example.com"],  # ドメイン限定
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600
)
```

### 2.2 Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/research/jobs")
@limiter.limit("10/minute")  # ユーザーあたり 1分 10回
async def start_research(...):
    pass
```

### 2.3 入力検証

```python
from pydantic import BaseModel, EmailStr, constr, validator

class ResearchRequest(BaseModel):
    keywords: list[str]  # 最大 10個
    sources: list[str]   # ホワイトリスト: ['mercari', 'ebay']
    days_back: int       # 1-365 範囲
    min_sales: int       # >= 1
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if len(v) > 10:
            raise ValueError('Max 10 keywords')
        if any(len(k) > 100 for k in v):
            raise ValueError('Keyword too long')
        return v
```

---

## 3. データセキュリティ

### 3.1 SQL Injection 対策

```python
# ❌ 危険
query = f"SELECT * FROM users WHERE email = '{email}'"
db.execute(query)

# ✅ 安全（ORM 使用）
user = db.query(User).filter(User.email == email).first()
```

### 3.2 パスワードハッシング

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# パスワードのハッシュ化
hashed_password = pwd_context.hash("user_password")

# パスワードの検証
is_valid = pwd_context.verify("user_password", hashed_password)
```

### 3.3 個人情報 (PII) 保護

- [x] Stripe を利用し、クレジットカード情報は自社DBに保存しない
- [x] ユーザーのメールアドレスは最小限のアクセス権限でのみ取得
- [x] ログファイルにパスワード、トークン、PII を出力しない（マスキング処理）

---

## 4. 運用セキュリティ

### 4.1 脆弱性スキャン

- [x] `pip-audit` または `Safety` をCI/CDパイプラインに組み込む
- [x] `npm audit` によるフロントエンドパッケージの脆弱性確認
- [x] 定期的な依存パッケージのアップデート（Dependabot の活用など）

### 4.2 インシデント対応

| 重大度分類 | 定義・影響範囲 | 対応時間（目標） | アクション・対応手順 |
|---|---|---|---|
| **Critical** | システムダウン、データ漏洩の発生・疑い | 15分以内 | サービスの一時停止、該当箇所の遮断、全ユーザーへの告知、対策チームの招集 |
| **High** | 一部機能の停止、特定の攻撃の検知 | 1時間以内 | アクセス制限の強化、パッチの緊急適用、影響範囲の調査 |
| **Medium** | 脆弱性の発見（非緊急）、スパム的な挙動 | 24時間以内 | 監視の強化、次期リリースでの修正対応 |
| **Low** | ベストプラクティスからの逸脱、軽微なバグ | 次回スプリント | バックログへの登録、通常フローでの修正 |

---

## 5. クラウド・インフラストラクチャ セキュリティ

- [x] Heroku 環境変数の適切な権限管理
- [x] データベース接続のSSL強制
- [x] Sentry 等の監視ツールにおける PII スクラブ（マスキング）設定
- [x] 定期的な自動バックアップと、暗号化された安全な保存先の確保

---

## 6. チェックリスト完了署名

- [ ] セキュリティレビュー完了日: _______________
- [ ] レビュアー署名: _______________
