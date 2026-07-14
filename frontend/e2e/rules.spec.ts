import { test, expect, type Page } from "@playwright/test";

async function login(page: Page) {
  await page.goto("/login");
  await page.getByLabel("Tên đăng nhập").fill("admin");
  await page.getByLabel("Mật khẩu").fill("admin");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
}

/**
 * E2E: Rule CRUD (yêu cầu backend Rule API chạy).
 */
test("tạo rule mới qua form", async ({ page }) => {
  await login(page);
  await page.getByRole("link", { name: "Rules" }).click();
  await expect(page.getByRole("heading", { name: "Rule Management" })).toBeVisible();

  await page.getByRole("button", { name: "Thêm Rule" }).click();
  const id = `E2E_RULE_${Date.now()}`;
  await page.getByLabel("ID").fill(id);
  await page.getByLabel("Tên").fill("E2E Test Rule");
  await page.getByRole("button", { name: "Tạo" }).click();

  await expect(page.getByText(id)).toBeVisible();
});
