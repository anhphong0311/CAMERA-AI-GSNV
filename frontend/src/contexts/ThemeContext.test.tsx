import { describe, expect, it } from "vitest";
import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider, useTheme } from "@/contexts/ThemeContext";

function Probe() {
  const { theme, toggle } = useTheme();
  return (
    <button onClick={toggle} data-testid="btn">
      {theme}
    </button>
  );
}

describe("ThemeContext", () => {
  it("toggle chuyển đổi light/dark và cập nhật class", async () => {
    render(
      <ThemeProvider>
        <Probe />
      </ThemeProvider>
    );
    const btn = screen.getByTestId("btn");
    const initial = btn.textContent;
    await act(async () => {
      await userEvent.click(btn);
    });
    expect(btn.textContent).not.toBe(initial);
    const isDark = document.documentElement.classList.contains("dark");
    expect(isDark).toBe(btn.textContent === "dark");
  });
});
