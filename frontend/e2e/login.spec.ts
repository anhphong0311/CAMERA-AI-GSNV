import { test, expect } from "@playwright/test";

/**
 * E2E: Login — đăng nhập bằng tài khoản demo, chuyển vào Dashboard.
 */
test("đăng nhập thành công và vào Dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill("admin");
  await page.getByLabel("Mật khẩu").fill("admin");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});

test("chưa đăng nhập bị chuyển về /login", async ({ page }) => {
  await page.goto("/alerts");
  await expect(page).toHaveURL(/\/login/);
});
