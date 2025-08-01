import { test, expect } from '@playwright/test';
test('login works', async ({ page }) => {
  await page.goto('/login');
  await page.fill('input[name=email]', 'admin@example.com');
  await page.fill('input[name=password]', 'password');
  await page.click('button[type=submit]');
  await expect(page).toHaveURL(/dashboard/);
});
