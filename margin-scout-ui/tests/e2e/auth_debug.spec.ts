import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.use({ baseURL: 'https://margin-scout-staging-frontend-ddc7bb12af5f.herokuapp.com' });

  test('register and login flow', async ({ page }) => {
    page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));
    page.on('pageerror', err => console.log('BROWSER ERROR:', err.message));
    
    const uniqueEmail = \	est_\@example.com\;

    // “o˜^
    await page.goto('/register');
    await page.fill('input#username', 'testuser');
    await page.fill('input#email', uniqueEmail);
    await page.fill('input#password', 'password123');
    await page.fill('input#passwordConfirm', 'password123');
    await page.click('button[type="submit"]');
    
    // Check if error-alert appears within 3 seconds
    try {
        const errorText = await page.locator('.error-alert').innerText({ timeout: 3000 });
        console.log('UI ERROR ALERT:', errorText);
    } catch(e) {}
    
    await expect(page).toHaveURL(/.*\/research/);
  });
});
