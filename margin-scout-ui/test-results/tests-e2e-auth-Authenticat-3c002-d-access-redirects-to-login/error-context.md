# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\e2e\auth.spec.ts >> Authentication Flow >> unauthorized access redirects to login
- Location: tests\e2e\auth.spec.ts:7:3

# Error details

```
Error: expect(page).toHaveURL(expected) failed

Expected pattern: /.*\/login/
Received string:  "https://margin-scout-staging-frontend-ddc7bb12af5f.herokuapp.com/research"
Timeout: 5000ms

Call log:
  - Expect "toHaveURL" with timeout 5000ms
    14 × unexpected value "https://margin-scout-staging-frontend-ddc7bb12af5f.herokuapp.com/research"

```

```yaml
- navigation:
  - link "MarginScout v2.1":
    - /url: /
  - link "リサーチ":
    - /url: /research
- main:
  - heading "📋 リサーチ条件設定" [level=1]
  - text: キーワード (カンマ区切り)
  - textbox "iPhone, Canon, Gucci"
  - text: 複数キーワードはカンマで区切ってください 取得元（複数選択可）
  - checkbox "mercari" [checked]
  - text: mercari
  - checkbox "yahoo_flea" [checked]
  - text: yahoo_flea
  - checkbox "yahoo_auction" [checked]
  - text: yahoo_auction
  - checkbox "hardoff" [checked]
  - text: hardoff 取得対象期間（日）
  - spinbutton: "90"
  - text: 最小販売数
  - spinbutton: "2"
  - button "🚀 リサーチ開始" [disabled]
- contentinfo:
  - paragraph: © 2026 MarginScout. All rights reserved.
- text: 📋 実行ログ (1 件)
- button "▼"
```

# Test source

```ts
  1  | // tests/e2e/auth.spec.ts
  2  | import { test, expect } from '@playwright/test';
  3  | 
  4  | test.describe('Authentication Flow', () => {
  5  |   test.use({ baseURL: 'https://margin-scout-staging-frontend-ddc7bb12af5f.herokuapp.com' });
  6  | 
  7  |   test('unauthorized access redirects to login', async ({ page }) => {
  8  |     await page.goto('/research');
> 9  |     await expect(page).toHaveURL(/.*\/login/);
     |                        ^ Error: expect(page).toHaveURL(expected) failed
  10 |     await expect(page.locator('h2')).toContainText('ログイン');
  11 |   });
  12 | 
  13 |   test('invalid login shows error message', async ({ page }) => {
  14 |     await page.goto('/login');
  15 |     await page.fill('input[type="email"]', 'wrong@example.com');
  16 |     await page.fill('input[type="password"]', 'invalidpass');
  17 |     await page.click('button[type="submit"]');
  18 |     await expect(page.locator('.error-alert')).toBeVisible();
  19 |   });
  20 | 
  21 |   test('register and login flow', async ({ page }) => {
  22 |     const uniqueEmail = `test_${Date.now()}@example.com`;
  23 | 
  24 |     // 登録
  25 |     await page.goto('/register');
  26 |     await page.fill('input#username', 'testuser');
  27 |     await page.fill('input#email', uniqueEmail);
  28 |     await page.fill('input#password', 'password123');
  29 |     await page.fill('input#passwordConfirm', 'password123');
  30 |     await page.click('button[type="submit"]');
  31 |     
  32 |     // 成功してリサーチ画面に遷移
  33 |     await expect(page).toHaveURL(/.*\/research/);
  34 | 
  35 |     // ログアウトをシミュレート
  36 |     await page.evaluate(() => localStorage.removeItem('refresh_token'));
  37 |     await page.reload();
  38 |     await page.goto('/research');
  39 |     await expect(page).toHaveURL(/.*\/login/);
  40 | 
  41 |     // ログイン
  42 |     await page.fill('input[type="email"]', uniqueEmail);
  43 |     await page.fill('input[type="password"]', 'password123');
  44 |     await page.click('button[type="submit"]');
  45 |     await expect(page).toHaveURL(/.*\/research/);
  46 |   });
  47 | });
  48 | 
```