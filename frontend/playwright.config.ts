import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E — chạy trên dev server (vite) đã build.
 * Yêu cầu backend chạy ở :8000 (proxy qua vite) để realtime hoạt động thật.
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
