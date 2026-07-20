import type { Page } from "@playwright/test";

// Matches backend/app/seed_admin.py's defaults -- override with the same
// env vars if you seeded a different admin.
export const ADMIN_EMAIL = process.env.TEST_ADMIN_EMAIL ?? "admin@migratepro.local";
export const ADMIN_PASSWORD = process.env.TEST_ADMIN_PASSWORD ?? "changeme123";

export async function login(page: Page) {
  await page.goto("/login");
  await page.fill('input[type="email"]', ADMIN_EMAIL);
  await page.fill('input[type="password"]', ADMIN_PASSWORD);
  await page.click('button[type="submit"]');
  // Client-side navigation, not a full page load -- wait on the URL itself
  // rather than a load-state-based helper (see AppShell's auth gate).
  await page.waitForFunction(() => location.pathname === "/", { timeout: 15_000 });
  await page.waitForLoadState("networkidle");
}
