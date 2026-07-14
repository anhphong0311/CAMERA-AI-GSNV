import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SeverityBadge } from "@/components/common/SeverityBadge";

describe("SeverityBadge", () => {
  it("hiển thị severity in hoa", () => {
    render(<SeverityBadge severity="high" />);
    expect(screen.getByText("HIGH")).toBeInTheDocument();
  });

  it("áp dụng class màu theo mức độ", () => {
    render(<SeverityBadge severity="CRITICAL" />);
    const el = screen.getByText("CRITICAL");
    expect(el.className).toContain("red");
  });
});
