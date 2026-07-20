import { expect, test } from "@playwright/test";
import { ADMIN_EMAIL, login } from "./helpers";

test.describe("authentication", () => {
  test("redirects an unauthenticated visitor to /login", async ({ page }) => {
    await page.goto("/");
    await page.waitForURL("**/login");
    await expect(page.locator('input[type="email"]')).toBeVisible();
  });

  test("shows an error on the wrong password", async ({ page }) => {
    await page.goto("/login");
    await page.fill('input[type="email"]', ADMIN_EMAIL);
    await page.fill('input[type="password"]', "definitely-wrong");
    await page.click('button[type="submit"]');
    await expect(page.getByText(/incorrect|incorrecta/i)).toBeVisible();
    // Still on /login -- a failed login must not grant access.
    expect(page.url()).toContain("/login");
  });

  test("logs in, survives a hard reload, and logs out", async ({ page }) => {
    await login(page);
    await expect(page.locator("h1")).toBeVisible();

    // Regression check: a hard reload re-evaluates auth from scratch (fresh
    // JS context, token read from localStorage at module load). This used
    // to race -- a page's own data-loading effect could fire an API request
    // before the token was attached, 401, and incorrectly log the user out
    // even though the stored session was valid. See api.ts's module-level
    // `authToken` initialization for the fix.
    await page.goto("/cases", { waitUntil: "networkidle" });
    expect(page.url()).not.toContain("/login");
    await expect(page.locator("h1")).toBeVisible();

    await page.click('button[aria-label="Cerrar sesión"], button[aria-label="Log out"]');
    await page.waitForURL("**/login");
  });

  test("forgot-password page accepts an email and shows a confirmation", async ({ page }) => {
    await page.goto("/forgot-password");
    await page.fill('input[type="email"]', ADMIN_EMAIL);
    await page.click('button[type="submit"]');
    await expect(page.getByText(/enviamos|sent/i)).toBeVisible();
  });
});
