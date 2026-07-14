/**
 * Logger hành động người dùng (client-side).
 *
 * Ghi log các sự kiện: đăng nhập, xem camera, replay, download, thay đổi rule.
 * Giữ trong bộ nhớ + localStorage (vòng đời phiên); có thể đẩy lên API sau.
 */

export type UserAction =
  | "login"
  | "logout"
  | "view_camera"
  | "replay"
  | "download"
  | "rule_change"
  | "roi_change"
  | "settings_change";

export interface ActionLog {
  action: UserAction;
  detail?: string;
  user?: string;
  ts: string;
}

const KEY = "aems.actionLogs";
const MAX = 500;

function read(): ActionLog[] {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "[]") as ActionLog[];
  } catch {
    return [];
  }
}

export function logAction(
  action: UserAction,
  detail?: string,
  user?: string
): void {
  const logs = read();
  logs.unshift({ action, detail, user, ts: new Date().toISOString() });
  if (logs.length > MAX) logs.length = MAX;
  localStorage.setItem(KEY, JSON.stringify(logs));
}

export function getActionLogs(): ActionLog[] {
  return read();
}

export function clearActionLogs(): void {
  localStorage.removeItem(KEY);
}
