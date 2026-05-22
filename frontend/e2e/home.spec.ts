import { expect, test } from "@playwright/test";

test.describe("Landing page", () => {
  test("loads without error", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.status()).not.toBe(500);
  });

  test("has a visible heading", async ({ page }) => {
    await page.goto("/");
    const heading = page.locator("h1, h2").first();
    await expect(heading).toBeVisible();
  });

  test("page title is set", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/.+/);
  });

  test("redirects unauthenticated users away from /dashboard", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await expect(page).not.toHaveURL(/\/dashboard/);
  });
});

test.describe("Login page", () => {
  test("loads without error", async ({ page }) => {
    const response = await page.goto("/login");
    expect(response?.status()).not.toBe(500);
  });

  test("contains a sign-in element", async ({ page }) => {
    await page.goto("/login");
    const signIn = page
      .getByRole("button", { name: /github|sign.?in/i })
      .or(page.getByRole("link", { name: /github|sign.?in/i }));
    await expect(signIn.first()).toBeVisible();
  });
});
