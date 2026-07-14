import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Severity } from "@/types";

/**
 * Gộp class Tailwind — utility chuẩn Shadcn UI.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Định dạng thời gian đầy đủ. */
export function formatDateTime(value?: string | number | Date | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("vi-VN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

/** Thời gian tương đối ngắn gọn (vd "5s trước"). */
export function formatRelative(value?: string | number | Date | null): string {
  if (!value) return "—";
  const then = new Date(value).getTime();
  if (Number.isNaN(then)) return "—";
  const diff = Math.max(0, Date.now() - then) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s trước`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m trước`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h trước`;
  return `${Math.floor(diff / 86400)}d trước`;
}

/** Định dạng khoảng thời gian giây → "1m 30s". */
export function formatDuration(seconds?: number | null): string {
  if (seconds == null) return "—";
  const s = Math.round(seconds);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  if (m < 60) return `${m}m ${rem}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

/** Màu badge theo severity. */
export function severityColor(severity: Severity | string): string {
  switch (String(severity).toUpperCase()) {
    case "CRITICAL":
      return "bg-red-600 text-white";
    case "HIGH":
      return "bg-orange-500 text-white";
    case "MEDIUM":
      return "bg-amber-500 text-black";
    case "LOW":
      return "bg-sky-500 text-white";
    default:
      return "bg-slate-500 text-white";
  }
}

/** Rút gọn số phần trăm an toàn. */
export function pct(value?: number | null): string {
  return value == null ? "—" : `${value.toFixed(0)}%`;
}
