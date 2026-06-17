import { test, expect } from '@playwright/test';

test.describe('Research Dashboard Flow', () => {
  // Test locally first
  test.use({ baseURL: 'http://localhost:5173' });

  test('multi-select options and conditions execution', async ({ page }) => {
    // Navigate to register to create a fresh user and get logged in
    const uniqueEmail = `test_${Date.now()}@example.com`;
    await page.goto('/register');
    await page.fill('input#username', 'testuser');
    await page.fill('input#email', uniqueEmail);
    await page.fill('input#password', 'password123');
    await page.fill('input#passwordConfirm', 'password123');
    await page.click('button[type="submit"]');
    
    // Check if we are on the research page
    await expect(page).toHaveURL(/.*\/research/);

    // Enter keyword
    await page.fill('input[placeholder="iPhone, Canon, Gucci"]', 'PlaywrightTest');

    // Uncheck "fixed_price" and check "auction" (as an example)
    await page.uncheck('input[value="fixed_price"]');
    await page.check('input[value="auction"]');

    // Uncheck "almost_new" and check "scratched"
    await page.uncheck('input[value="almost_new"]');
    await page.check('input[value="scratched"]');

    // Submit the form
    await page.click('button[type="submit"]');

    // It should redirect to monitoring page
    await expect(page).toHaveURL(/.*\/monitor\/.+/);
    await expect(page.locator('h1')).toContainText('実行中モニター');
  });
});
