import { defineConfig, devices } from "@playwright/test";

// These tests exercise the real app against a real backend -- there's no
// mocking layer. Start the backend yourself first (with an admin seeded via
// `python -m app.seed_admin`, see backend/README section "Desarrollo local")
// before running `npm run test:e2e`. Playwright only manages the frontend
// dev server here; orchestrating the Python backend from a Node config
// would need a second process type and its own venv activation, which isn't
// worth it for local/manual test runs.
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false, // tests share one seeded admin account/session state
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: {
    command: "npm run dev",
    url: baseURL,
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
