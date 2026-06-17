# MarginScout SaaS - 認証・認可設計書

**バージョン**: 1.0  
**作成日**: 2026-06-16

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. 認証・認可概要

### 1.1 定義

**認証 (Authentication)**: あなたは誰か？
- ユーザー登録・ログイン
- パスワード検証
- トークン発行

**認可 (Authorization)**: あなたは何ができるか？
- user_id ベースのアクセス制御
- プラン種別による制限（Basic/Pro）
- リソースアクセス権限

---

## 2. 認証フロー

### 2.1 登録フロー

【UI: 登録画面】 
ユーザー入力:
- Email
- Password
↓ POST /auth/register

【Backend】
- Email 形式チェック
- Email 重複確認
- Password ハッシング (bcrypt)
- users テーブルに保存
- JWT トークン発行
↓ レスポンス

【Frontend】
- トークンを localStorage に保存
- ユーザーをダッシュボードへリダイレクト

### 2.2 ログインフロー

【UI: ログイン画面】 
ユーザー入力:
- Email
- Password
↓ POST /auth/login

【Backend】
- Email で users テーブルから検索
- Password ハッシング比較
- マッチ → JWT トークン発行
- マッチしない → 401 Unauthorized
↓ レスポンス

【Frontend】
- トークン保存
- ダッシュボード表示

### 2.3 JWT トークン

【トークン構造】 
Header: { "alg": "HS256", "typ": "JWT" } 
Payload: { "user_id": "uuid-abc123", "email": "user@example.com", "exp": 1719100000, "iat": 1719013600 } 
Signature: HMAC-SHA256(header.payload, secret)

【使用方法】 
リクエストヘッダー: `Authorization: Bearer eyJhbGciOiJIUzI1NiIs...`

---

## 3. エンドポイント

### 3.1 認証エンドポイント

| メソッド | エンドポイント | 説明 |
|---|---|---|
| POST | /auth/register | ユーザー登録 |
| POST | /auth/login | ログイン |
| POST | /auth/logout | ログアウト |
| POST | /auth/refresh-token | トークン更新 |
| POST | /auth/password-reset | パスワードリセット |

### 3.2 実装例

```python
from fastapi import FastAPI, HTTPException, Header, Depends
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key"

# ========== 登録 ==========
@app.post("/auth/register")
async def register(email: str, password: str):
    # Email 重複確認
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Password ハッシング
    hashed_password = pwd_context.hash(password)
    
    # ユーザー作成
    new_user = User(email=email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    
    # トークン発行
    token = create_token(new_user.user_id)
    
    return {
        "user_id": new_user.user_id,
        "email": new_user.email,
        "token": token
    }

# ========== ログイン ==========
@app.post("/auth/login")
async def login(email: str, password: str):
    # ユーザー検索
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Password 検証
    if not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # トークン発行
    token = create_token(user.user_id)
    
    return {
        "user_id": user.user_id,
        "email": user.email,
        "token": token
    }

# ========== トークン生成 ==========
def create_token(user_id: str):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

# ========== トークン検証 ==========
def verify_token(token: str = Header(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401)
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

# ========== 認証が必要なエンドポイント ==========
@app.get("/api/research/jobs")
async def get_jobs(user_id: str = Depends(verify_token)):
    jobs = db.query(ResearchJob).filter(
        ResearchJob.user_id == user_id
    ).all()
    return jobs
```

---

## 4. ログアウト・セッション管理

### 4.1 ログアウト
【Frontend】
1. localStorage から token 削除
2. /auth/logout 呼び出し（オプション）
3. ログイン画面へリダイレクト

【Backend】
- 不要（ステートレス）
- token は自動的に無効（有効期限切れ待ち）

### 4.2 トークン更新
【用途】
ユーザーが長時間ブラウザを開いている場合、トークンの有効期限を延長

【エンドポイント】
POST /auth/refresh-token
リクエスト: 古い token
レスポンス: 新しい token

---

## 5. セキュリティ考慮事項

### 5.1 Password ハッシング
❌ 平文で保存
❌ MD5・SHA1 使用
✅ bcrypt 使用（推奨）
✅ Cost factor: 12

### 5.2 Token セキュリティ
✅ HTTPS のみで転送
✅ HttpOnly Cookie に保存（XSS 対策）または localStorage（CSRF 対策）
✅ Refresh Token 分離（オプション）
✅ Token 有効期限: 24時間

### 5.3 Password リセット
【フロー】
1. ユーザー: Email 入力
2. Backend: リセットリンク生成（24時間有効）
3. Backend: Email 送信
4. ユーザー: リンククリック
5. Frontend: 新 Password 入力
6. Backend: Password 更新

---

## 6. テスト項目
✅ 登録: 正常系・重複 Email・invalid Password
✅ ログイン: 正常系・存在しない Email・誤り Password
✅ Token: 有効・期限切れ・改ざん
✅ ログアウト: token 削除確認
✅ CORS: 許可ドメインのみ

---

## 7. 参照
- docs/SAAS_MULTITENANCY_DESIGN.md (user_id 制御)
- docs/SAAS_SECURITY_CHECKLIST.md (セキュリティ全般)
