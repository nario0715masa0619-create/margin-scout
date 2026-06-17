# MarginScout SaaS - Phase 1 Frontend 実装ガイド

**バージョン**: 1.0  
**作成日**: 2026-06-16  
**スタック**: Vue 3 (Composition API) + TypeScript + Pinia + Vue Router + Axios + Playwright

---

## 1. プロジェクト構成と環境設定

### 1.1 ディレクトリ構成

```text
margin-scout-ui/
├── src/
│   ├── assets/
│   ├── components/
│   │   ├── auth/            # 認証関連コンポーネント
│   │   │   ├── LoginForm.vue
│   │   │   ├── RegisterForm.vue
│   │   │   └── ResetPasswordForm.vue
│   │   └── common/
│   ├── composables/         # 再利用ロジック
│   │   ├── useAuth.ts
│   │   └── useUser.ts
│   ├── router/
│   │   └── index.ts         # ルーティング + ナビゲーションガード
│   ├── services/
│   │   └── api.ts           # Axios インスタンス + インターセプター
│   ├── stores/
│   │   ├── auth.ts          # Pinia: トークンと認証状態
│   │   └── user.ts          # Pinia: ユーザー情報
│   ├── views/
│   │   ├── LoginView.vue
│   │   ├── RegisterView.vue
│   │   └── DashboardView.vue
│   ├── App.vue
│   └── main.ts
├── tests/
│   └── e2e/                 # Playwright テスト
├── .env.example
├── package.json
└── tsconfig.json
```

### 1.2 パッケージと依存関係の更新

```bash
npm install axios pinia vue-router
npm install -D @playwright/test @types/node typescript
```

### 1.3 環境変数 (`.env.example`)

```env
VITE_API_BASE_URL=https://margin-scout.example.com/api/v1
VITE_ENVIRONMENT=development
```

### 1.4 TypeScript 型定義 (厳密性チェック)

```typescript
// src/types/auth.d.ts
export interface User {
  id: string;
  email: string;
  plan_type: 'free' | 'basic' | 'pro';
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}
```

---

## 2. セキュリティベストプラクティス（最重要）

### 2.1 トークンの保存場所
- **Access Token**: メモリ内 (Pinia store) または `SessionStorage` に保存。
- **Refresh Token**: 本来は HttpOnly Cookie が最も安全ですが、SaaS初期フェーズでの実装の容易さを優先し `LocalStorage` に保存し、XSS攻撃リスクを認識した上でVueのテンプレートエスケープを活用します。

### 2.2 CSRF対策
- JWTベースの認証を用いるため、Authorization Header での通信となりCSRFのリスクは本質的に低減されます（Cookieの自動送信がないため）。

---

## 3. Pinia ストア実装

### 3.1 Auth ストア (`src/stores/auth.ts`)

```typescript
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  // State
  const accessToken = ref<string | null>(null);
  const refreshToken = ref<string | null>(localStorage.getItem('refreshToken'));

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value);

  // Actions
  function setTokens(access: string, refresh: string) {
    accessToken.value = access;
    refreshToken.value = refresh;
    localStorage.setItem('refreshToken', refresh);
  }

  function clearTokens() {
    accessToken.value = null;
    refreshToken.value = null;
    localStorage.removeItem('refreshToken');
  }

  return {
    accessToken,
    refreshToken,
    isAuthenticated,
    setTokens,
    clearTokens
  };
});
```

### 3.2 User ストア (`src/stores/user.ts`)

```typescript
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { User } from '@/types/auth';

export const useUserStore = defineStore('user', () => {
  const currentUser = ref<User | null>(null);

  function setUser(user: User) {
    currentUser.value = user;
  }

  function clearUser() {
    currentUser.value = null;
  }

  return { currentUser, setUser, clearUser };
});
```

---

## 4. Axios インターセプターとバックグラウンドリフレッシュ

API通信時にJWTを付与し、401 (Unauthorized) 発生時に自動で Refresh Token を使って Access Token を再取得します。

```typescript
// src/services/api.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';
import router from '@/router';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' }
});

// リクエストインターセプター: Access Token を付与
api.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  if (authStore.accessToken) {
    config.headers.Authorization = `Bearer ${authStore.accessToken}`;
  }
  return config;
});

// レスポンスインターセプター: 401 ハンドリングとリフレッシュ処理
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // 401 エラーで、かつリトライしていない場合
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const authStore = useAuthStore();

      if (authStore.refreshToken) {
        try {
          // Token リフレッシュリクエスト
          const { data } = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/refresh`, {
            refresh_token: authStore.refreshToken
          });

          // 新しいトークンをセット
          authStore.setTokens(data.access_token, data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          
          // 元のリクエストを再試行
          return api(originalRequest);
        } catch (refreshError) {
          // リフレッシュ失敗時は強制ログアウト
          authStore.clearTokens();
          router.push('/login');
          return Promise.reject(refreshError);
        }
      } else {
        // Refresh Token がない場合はログアウト
        authStore.clearTokens();
        router.push('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

---

## 5. Vue Router ガード

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { requiresGuest: true }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { requiresAuth: true }
    },
    // その他のルート (既存のリサーチ画面等) には requiresAuth: true を付与
  ]
});

// グローバルナビゲーションガード
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // 認証が必要だが、認証されていない場合
    next('/login');
  } else if (to.meta.requiresGuest && authStore.isAuthenticated) {
    // ゲスト用画面 (ログイン等) にアクセスしようとしたが、既に認証済みの場合
    next('/dashboard');
  } else {
    next();
  }
});

export default router;
```

---

## 6. 認証コンポーネント (LoginForm)

```html
<!-- src/components/auth/LoginForm.vue -->
<template>
  <div class="login-form">
    <h2>ログイン</h2>
    <form @submit.prevent="handleLogin">
      <div>
        <label>Email</label>
        <input type="email" v-model="email" required />
      </div>
      <div>
        <label>Password</label>
        <input type="password" v-model="password" required />
      </div>
      <button type="submit" :disabled="loading">
        {{ loading ? 'ログイン中...' : 'ログイン' }}
      </button>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAuth } from '@/composables/useAuth';

const email = ref('');
const password = ref('');
const loading = ref(false);
const errorMessage = ref('');
const { login } = useAuth();

async function handleLogin() {
  loading.value = true;
  errorMessage.value = '';
  try {
    await login(email.value, password.value);
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'ログインに失敗しました';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.error { color: red; }
</style>
```

---

## 7. Composables (共通ロジック)

```typescript
// src/composables/useAuth.ts
import api from '@/services/api';
import { useAuthStore } from '@/stores/auth';
import { useUserStore } from '@/stores/user';
import { useRouter } from 'vue-router';

export function useAuth() {
  const authStore = useAuthStore();
  const userStore = useUserStore();
  const router = useRouter();

  async function login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password });
    authStore.setTokens(data.access_token, data.refresh_token);
    userStore.setUser({ id: data.user_id, email: data.email, plan_type: data.plan_type });
    router.push('/dashboard');
  }

  function logout() {
    authStore.clearTokens();
    userStore.clearUser();
    router.push('/login');
  }

  return { login, logout };
}
```

---

## 8. 既存UI との統合ポイント

既存の MarginScout のヘッダーコンポーネントに最小限の変更を加えます。

```html
<!-- src/components/layout/AppHeader.vue の変更イメージ -->
<template>
  <header>
    <div class="logo">MarginScout</div>
    <div class="user-info" v-if="authStore.isAuthenticated">
      <span>{{ userStore.currentUser?.email }} ({{ userStore.currentUser?.plan_type }})</span>
      <button @click="logout">ログアウト</button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth';
import { useUserStore } from '@/stores/user';
import { useAuth } from '@/composables/useAuth';

const authStore = useAuthStore();
const userStore = useUserStore();
const { logout } = useAuth();
</script>
```

---

## 9. Playwright E2E テスト

### 9.1 アクセス制御の検証
```typescript
// tests/e2e/access-control.spec.ts
import { test, expect } from '@playwright/test';

test('ゲストユーザーはダッシュボードにアクセスできずログインにリダイレクトされる', async ({ page }) => {
  await page.goto('/dashboard');
  // 認証ガードにより /login にリダイレクトされることを確認
  await expect(page).toHaveURL(/.*\/login/);
});
```

### 9.2 ログインフローの検証
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test('正しい情報でログインするとダッシュボードに遷移する', async ({ page }) => {
  await page.goto('/login');

  await page.fill('input[type="email"]', 'test@example.com');
  await page.fill('input[type="password"]', 'password123');
  await page.click('button[type="submit"]');

  // ダッシュボード遷移の確認
  await expect(page).toHaveURL(/.*\/dashboard/);
  // ヘッダーにユーザーのメールアドレスが表示されること
  await expect(page.locator('.user-info')).toContainText('test@example.com');
});
```

---

## ⚠️ 実装時の注意点

1. **初期化時の認証状態の復元**: ページリロード時、`LocalStorage` の Refresh Token を用いて Access Token を再取得するロジックを `App.vue` の `onMounted` 等で呼び出す必要があります。
2. **既存 API のエンドポイント調整**: すべてのリクエストは `/api/v1` 配下になり、`api.ts` を経由する必要があります。既存コードで `axios.get` などと直接書いていた部分は、`api.get` に置き換えてください。
3. **CORS設定**: Backend 側の `ALLOWED_ORIGINS` と Frontend のホスト名が一致していることを必ず確認してください。
