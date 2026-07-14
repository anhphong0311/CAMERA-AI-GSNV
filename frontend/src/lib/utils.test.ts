import { describe, expect, it } from "vitest";
import {
  cn,
  formatDuration,
  formatRelative,
  pct,
  severityColor,
} from "@/lib/utils";

describe("utils", () => {
  it("cn gộp và loại bỏ class trùng", () => {
    const hidden = false as boolean;
    expect(cn("p-2", "p-4")).toBe("p-4");
    expect(cn("text-sm", hidden && "hidden", "font-bold")).toBe("text-sm font-bold");
  });

  it("formatDuration định dạng giây/phút/giờ", () => {
    expect(formatDuration(45)).toBe("45s");
    expect(formatDuration(90)).toBe("1m 30s");
    expect(formatDuration(3660)).toBe("1h 1m");
    expect(formatDuration(null)).toBe("—");
  });

  it("pct hiển thị phần trăm", () => {
    expect(pct(42.7)).toBe("43%");
    expect(pct(null)).toBe("—");
  });

  it("severityColor trả về class theo mức độ", () => {
    expect(severityColor("CRITICAL")).toContain("red");
    expect(severityColor("high")).toContain("orange");
    expect(severityColor("unknown")).toContain("slate");
  });

  it("formatRelative trả về chuỗi tương đối", () => {
    expect(formatRelative(new Date().toISOString())).toContain("trước");
    expect(formatRelative(null)).toBe("—");
  });
});
