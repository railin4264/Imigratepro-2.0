import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test.describe("core pages render for a logged-in user", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  for (const path of ["/clients", "/cases", "/services", "/forms", "/documents", "/appointments", "/billing", "/stats"]) {
    test(`${path} loads without redirecting to /login or throwing`, async ({ page }) => {
      const errors: string[] = [];
      page.on("pageerror", (err) => errors.push(String(err)));

      await page.goto(path, { waitUntil: "networkidle" });
      expect(page.url()).not.toContain("/login");
      await expect(page.locator("h1")).toBeVisible();
      expect(errors).toEqual([]);
    });
  }
});

test.describe("case detail shows appointments and invoices inline", () => {
  test("creating a case exposes Citas/Facturas sections when expanded", async ({ page }) => {
    await login(page);
    await page.goto("/cases", { waitUntil: "networkidle" });

    const caseNumber = `E2E-${Date.now()}`;
    await page.click('button:has-text("Nuevo caso"), button:has-text("New case")');
    // The case-number field has no `type` attribute (defaults to text), so
    // `input[type="text"]` wouldn't match it as a CSS attribute selector --
    // it's the only `required` field in this form, so target that instead.
    await page.fill("form input[required]", caseNumber);
    await page.click('button[type="submit"]');

    // Reload from scratch rather than trusting the SPA's in-memory refresh --
    // proves the case actually persisted server-side, not just that local
    // state updated, and sidesteps Next dev-mode HMR occasionally clobbering
    // in-flight component state mid-test.
    await page.goto("/cases", { waitUntil: "networkidle" });
    await expect(page.getByText(caseNumber)).toBeVisible();

    await page.click(`text=${caseNumber}`);
    // Scope to headings -- the sidebar nav also has links with this text.
    await expect(page.getByRole("heading", { name: /Citas|Appointments/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Facturas|Invoices/ })).toBeVisible();
  });
});
