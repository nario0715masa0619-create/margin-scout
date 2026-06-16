# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\e2e\auth.spec.ts >> Authentication Flow >> invalid login shows error message
- Location: tests\e2e\auth.spec.ts:13:3

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: page.fill: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('input[type="email"]')

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - navigation [ref=e4]:
    - link "MarginScout v2.1" [ref=e6] [cursor=pointer]:
      - /url: /
    - link "リサーチ" [ref=e8] [cursor=pointer]:
      - /url: /research
  - main [ref=e9]
  - contentinfo [ref=e10]:
    - paragraph [ref=e11]: © 2026 MarginScout. All rights reserved.
  - generic [ref=e13] [cursor=pointer]:
    - generic [ref=e14]: 📋 実行ログ (1 件)
    - button "▼" [ref=e15]
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
  9  |     await expect(page).toHaveURL(/.*\/login/);
  10 |     await expect(page.locator('h2')).toContainText('ログイン');
  11 |   });
  12 | 
  13 |   test('invalid login shows error message', async ({ page }) => {
  14 |     await page.goto('/login');
> 15 |     await page.fill('input[type="email"]', 'wrong@example.com');
     |                ^ Error: page.fill: Test timeout of 30000ms exceeded.
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