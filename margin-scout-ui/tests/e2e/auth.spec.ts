// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.use({ baseURL: 'http://localhost:5173' });

  test('unauthorized access redirects to login', async ({ page }) => {
    await page.goto('/research');
    await expect(page).toHaveURL(/.*\/login/);
    await expect(page.locator('h2')).toContainText('ログイン');
  });

  test('invalid login shows error message', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'wrong@example.com');
    await page.fill('input[type="password"]', 'invalidpass');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error-alert')).toBeVisible();
  });

  test('register and login flow', async ({ page }) => {
    const uniqueEmail = `test_${Date.now()}@example.com`;

    // 登録
    await page.goto('/register');
    await page.fill('input#username', 'testuser');
    await page.fill('input#email', uniqueEmail);
    await page.fill('input#password', 'password123');
    await page.fill('input#passwordConfirm', 'password123');
    await page.click('button[type="submit"]');
    
    // 成功してリサーチ画面に遷移
    await expect(page).toHaveURL(/.*\/research/);

    // ログアウトをシミュレート
    await page.evaluate(() => localStorage.removeItem('refresh_token'));
    await page.reload();
    await page.goto('/research');
    await expect(page).toHaveURL(/.*\/login/);

    // ログイン
    await page.fill('input[type="email"]', uniqueEmail);
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/.*\/research/);
  });
});
