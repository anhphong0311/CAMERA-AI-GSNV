import { test, expect, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill("admin");
  await page.getByLabel("Mật khẩu").fill("admin");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

/**
 * E2E: View Camera + nhận Alert realtime (yêu cầu backend chạy để có dữ liệu WS).
 */
test("xem Live Camera grid", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Live Camera" }).click();
  await expect(page.getByRole("heading", { name: "Live Camera" })).toBeVisible();
  await expect(page.locator("canvas").first()).toBeVisible();
});

test("mở Alert Center", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Alerts" }).click();
  await expect(page.getByRole("heading", { name: "Alert Center" })).toBeVisible();
});

test("Replay hiển thị trình phát video", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Replay" }).click();
  await expect(page.getByRole("heading", { name: "Video Replay" })).toBeVisible();
});
