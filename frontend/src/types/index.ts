/**
 * Kiểu dữ liệu dùng chung toàn Dashboard.
 * Chỉ mô tả shape dữ liệu API/WebSocket — không chứa business logic.
 */

export interface ApiResponse<T> {
  data: T | null;
  meta?: Record<string, unknown> | null;
  error?: { code: string; message: string } | null;
}

export type Role = "admin" | "supervisor" | "viewer";

export interface AuthUser {
  id: string;
  username: string;
  role: Role;
  fullName?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";

export type EventStatus =
  | "NEW"
  | "VALIDATING"
  | "PROCESSING"
  | "SNAPSHOT_CREATED"
  | "VIDEO_CREATED"
  | "NOTIFICATION_SENT"
  | "COMPLETED"
  | "FAILED";

export interface CameraStatus {
  camera_id: number;
  code?: string;
  name: string;
  status: "online" | "offline" | string;
  fps: number;
  enabled?: boolean;
}

export interface ManagedCamera {
  id: number;
  code: string;
  name: string | null;
  location: string | null;
  rtsp_main: string;
  rtsp_sub: string | null;
  status: string;
  fps: number;
  enabled: boolean;
}

export interface CameraFrame {
  camera_id: number;
  frame_id: number;
  timestamp: string;
  width: number;
  height: number;
  image_base64: string;
}

export interface DetectionObject {
  track_id: number | null;
  label: string;
  confidence: number;
  bbox: [number, number, number, number]; // x, y, w, h (0..1)
  roi?: string;
  interacting?: boolean;
  inferred?: boolean;
}

export interface DetectionFrame {
  camera_id: number;
  fps: number;
  objects: DetectionObject[];
  ts: string;
  phone_interaction?: boolean;
}

export interface TrackInfo {
  track_id: number;
  camera_id: number;
  roi: string;
  duration: number;
  speed: number;
  direction: string;
  stationary_time: number;
}

export interface TrackingFrame {
  camera_id: number;
  tracks: TrackInfo[];
  ts: string;
}

export interface AlertEvent {
  event_id: string;
  camera_id: number;
  camera_name?: string;
  track_id: number;
  rule_id: string;
  severity: Severity;
  confidence: number;
  duration: number;
  roi?: string;
  status: EventStatus | string;
  ts?: string;
  snapshot?: { path: string } | null;
  video?: { path: string } | null;
  metadata?: Record<string, unknown>;
}

export interface SystemMetrics {
  cpu_percent: number | null;
  ram_percent?: number | null;
  ram_used_mb?: number | null;
  ram_total_mb?: number | null;
  disk_percent?: number | null;
  disk_used_gb?: number | null;
  disk_total_gb?: number | null;
  net_sent_kbps?: number | null;
  net_recv_kbps?: number | null;
  gpu_percent?: number | null;
  vram_used_mb?: number | null;
  vram_total_mb?: number | null;
  vram_percent?: number | null;
  gpu_available?: boolean;
}

export interface Overview {
  cameras_online: number;
  cameras_offline: number;
  cameras_total: number;
  ai_fps: number;
  today_alerts: number;
  today_violations: number;
  system: SystemMetrics;
}

export interface Rule {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  severity: Severity | string;
  priority: number;
  cooldown?: number | null;
  category?: string;
}

export interface Employee {
  id: string;
  name: string;
  department?: string;
  track_ids?: number[];
  performance_score?: number;
  working_time?: number;
  violation_time?: number;
}

export interface ROIPoint {
  x: number;
  y: number;
}

export interface ROI {
  id: string;
  name: string;
  camera_id: number;
  type: "polygon" | "rectangle";
  points: ROIPoint[];
}

export type WsChannel =
  | "hello"
  | "pong"
  | "system"
  | "detection"
  | "tracking"
  | "alert"
  | "camera_status";

export interface WsMessage<T = unknown> {
  channel: WsChannel;
  data: T;
}
