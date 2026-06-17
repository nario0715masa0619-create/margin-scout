# MarginScout SaaS - 課金・サブスク設計書

**バージョン**: 1.0  
**作成日**: 2026-06-16

## ⚠️ スコープ明記

MarginScout は SaaS 化後もリサーチツールであり、Sell API / 出品 / 在庫 / 注文管理はスコープ外です。

---

## 1. プラン構成

### 1.1 3 段階プラン

| 項目 | Free | Basic | Professional |
|---|---|---|---|
| 月額料金 | ¥0 | ¥980 | ¥2,980 |
| 月間リサーチ数 | 3 | 50 | 無制限 |
| CSV 出力 | ✅ | ✅ | ✅ |
| データ保持期間 | 7日 | 30日 | 90日 |
| サポート | | メール | メール+チャット |
| 分析機能 | | | ✅ |

### 1.2 利用開始フロー

【新規ユーザー】
1. 登録
2. Free プラン自動割り当て（クレジットカード不要）
3. 3回のリサーチ実施可能
4. 4回目でプラン選択画面表示

【プラン選択】 
→ Basic / Professional を選択 
→ クレジットカード入力（Stripe） 
→ 決済実行 
→ プラン有効化

---

## 2. 決済システム

### 2.1 Stripe 連携

**Stripe を使用する理由**:
✅ 日本の支払い方法対応（クレジットカード中心） 
✅ サブスク管理が簡単 
✅ Webhook で自動処理 
✅ 手数料: 3.6% + ¥0.01/件 
✅ 日本語サポート

### 2.2 API キー管理

本番環境:
- STRIPE_API_KEY: 環境変数
- STRIPE_WEBHOOK_SECRET: 環境変数

テスト環境:
- テスト用 API キー使用
- テストカード: 4242 4242 4242 4242

---

## 3. 課金フロー

### 3.1 サブスク開始

【UI】
1. ユーザー: プラン選択（Basic/Pro）
2. UI: Stripe Checkout フォーム表示
3. カード情報入力
4. Email 確認
↓ Stripe で決済処理

【Webhook】 
5. Backend: Stripe Webhook 受取 イベント: customer.subscription.created 
6. Backend: subscriptions テーブル更新 
7. Backend: plan_type を users テーブル更新

【Response】 
8. Frontend: 成功メッセージ 
9. Frontend: ユーザーをダッシュボードへ

### 3.2 サブスク更新（毎月）

【毎月の自動決済】
1. Stripe が自動で請求
2. Backend が Webhook で通知受取
3. Backend: subscription 更新（current_period_end 延長）

【失敗時】
1. Stripe: Webhook で失敗通知
2. Backend: subscription status = "past_due"
3. Frontend: 支払い方法更新画面表示

### 3.3 サブスク解約

【ユーザー操作】
1. UI: サブスク管理画面
2. UI: "キャンセル" ボタン
3. UI: 確認ダイアログ
↓ POST /billing/cancel-subscription

【Backend】 
4. Backend: Stripe API で subscription.cancel() 
5. Backend: Webhook 受取（customer.subscription.deleted） 
6. Backend: subscriptions テーブル更新
   - status = "cancelled"
   - cancelled_at = 現在時刻

【Response】 
7. Frontend: "キャンセルしました" 
8. Frontend: plan_type を Free に戻す 
9. Frontend: 月間リサーチ数リセット

---

## 4. エンドポイント

### 4.1 課金管理 API

| メソッド | エンドポイント | 説明 |
|---|---|---|
| GET | /billing/current-plan | 現在のプラン |
| POST | /billing/subscribe | サブスク開始 |
| GET | /billing/subscription | サブスク情報 |
| POST | /billing/cancel-subscription | サブスク解約 |
| POST | /billing/update-payment | 支払い方法変更 |
| GET | /billing/invoices | 請求書一覧 |

### 4.2 実装例

```python
import stripe

stripe.api_key = os.getenv("STRIPE_API_KEY")

# ========== サブスク作成 ==========
@app.post("/billing/subscribe")
async def subscribe(
    plan_type: str,  # "basic" or "pro"
    token: str = Header(...)
):
    user_id = verify_token(token)
    user = db.query(User).filter(User.user_id == user_id).first()
    
    # Stripe Customer 作成
    if not user.stripe_customer_id:
        customer = stripe.Customer.create(email=user.email)
        user.stripe_customer_id = customer.id
        db.commit()
    
    # Price ID マッピング
    price_ids = {
        "basic": "price_1basic",
        "pro": "price_1pro"
    }
    
    # Subscription 作成
    subscription = stripe.Subscription.create(
        customer=user.stripe_customer_id,
        items=[{"price": price_ids[plan_type]}],
        payment_behavior="default_incomplete",
        expand=["latest_invoice.payment_intent"]
    )
    
    return {
        "subscription_id": subscription.id,
        "client_secret": subscription.latest_invoice.payment_intent.client_secret
    }

# ========== Webhook ハンドラ ==========
@app.post("/billing/webhook")
async def webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except:
        raise HTTPException(status_code=400)
    
    # イベント処理
    if event["type"] == "customer.subscription.created":
        subscription = event["data"]["object"]
        user = db.query(User).filter(
            User.stripe_customer_id == subscription["customer"]
        ).first()
        
        # DB 更新
        new_sub = Subscription(
            subscription_id=subscription["id"],
            user_id=user.user_id,
            stripe_subscription_id=subscription["id"],
            plan_type="basic" if "basic" in str(subscription["items"]["data"][0]["price"]) else "pro",
            status="active",
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"])
        )
        db.add(new_sub)
        user.plan_type = new_sub.plan_type
        db.commit()
    
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        sub = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription["id"]
        ).first()
        if sub:
            sub.status = "cancelled"
            sub.cancelled_at = datetime.utcnow()
            user = db.query(User).filter(User.user_id == sub.user_id).first()
            user.plan_type = "free"
            db.commit()
    
    return {"status": "success"}

# ========== 現在のプラン取得 ==========
@app.get("/billing/current-plan")
async def get_plan(token: str = Header(...)):
    user_id = verify_token(token)
    user = db.query(User).filter(User.user_id == user_id).first()
    
    plan_limits = {
        "free": {"monthly_limit": 3, "retention_days": 7},
        "basic": {"monthly_limit": 50, "retention_days": 30},
        "pro": {"monthly_limit": float("inf"), "retention_days": 90}
    }
    
    return {
        "plan_type": user.plan_type,
        "limits": plan_limits[user.plan_type]
    }
```

---

## 5. 使用量制限実装

### 5.1 月間リサーチ数チェック
```python
# リサーチ開始時
@app.post("/api/research/jobs")
async def start_research(
    keywords: list,
    token: str = Header(...)
):
    user_id = verify_token(token)
    user = db.query(User).filter(User.user_id == user_id).first()
    
    # 月間使用量取得
    current_month_start = datetime.now().replace(day=1)
    monthly_jobs = db.query(ResearchJob).filter(
        ResearchJob.user_id == user_id,
        ResearchJob.created_at >= current_month_start
    ).count()
    
    # プラン別上限
    limits = {"free": 3, "basic": 50, "pro": float("inf")}
    limit = limits[user.plan_type]
    
    # チェック
    if monthly_jobs >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly limit {limit} reached. Upgrade your plan."
        )
    
    # リサーチ実行
    job = ResearchJob(...)
    db.add(job)
    db.commit()
    
    return {"job_id": job.job_id}
```

---

## 6. テスト項目
✅ Free プラン: 3回制限、7日保持
✅ Basic プラン: 50回、30日保持
✅ Pro プラン: 無制限
✅ Stripe 決済: 正常系・失敗系
✅ Webhook: 購読・更新・解約
✅ 月間リセット: 1日に自動リセット

---

## 7. 参照
- docs/SAAS_DATABASE_DESIGN.md (subscriptions テーブル)
- docs/SAAS_SECURITY_CHECKLIST.md (API キー管理)
