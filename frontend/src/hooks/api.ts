import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { apiClient, unwrap } from "@/lib/api";
import { logAction } from "@/lib/logger";
import type {
  AlertEvent,
  CameraFrame,
  CameraStatus,
  Employee,
  ManagedCamera,
  Overview,
  Rule,
  SystemMetrics,
} from "@/types";

/** Gọi GET và unwrap ApiResponse; ném lỗi nếu thất bại. */
async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const res = await apiClient.get(url, { params });
  return unwrap<T>(res.data);
}

// ----- Overview / System / Cameras / Alerts (realtime REST snapshot) -----
export function useOverview() {
  return useQuery({
    queryKey: ["overview"],
    queryFn: () => get<Overview>("/realtime/overview"),
    refetchInterval: 5000,
  });
}

export function useSystemSnapshot() {
  return useQuery({
    queryKey: ["system"],
    queryFn: () => get<SystemMetrics>("/realtime/system"),
    refetchInterval: 5000,
  });
}

export function useCameras() {
  return useQuery({
    queryKey: ["cameras"],
    queryFn: () => get<CameraStatus[]>("/realtime/cameras"),
    refetchInterval: 10000,
  });
}

/** Camera thật từ DB (Camera Service). */
export function useManagedCameras() {
  return useQuery({
    queryKey: ["managed-cameras"],
    queryFn: async () => {
      const rows = await get<ManagedCamera[]>("/cameras");
      return rows.map(
        (c): CameraStatus => ({
          camera_id: c.id,
          name: c.name ?? c.code,
          status: c.status === "online" ? "online" : "offline",
          fps: c.fps ?? 0,
        })
      );
    },
    refetchInterval: 10000,
  });
}

/** Poll frame JPEG mới nhất từ RTSP worker (stagger theo cameraId để tránh burst). */
export function useCameraFrame(cameraId: number, enabled = true) {
  return useQuery({
    queryKey: ["camera-frame", cameraId],
    queryFn: () => get<CameraFrame>(`/cameras/${cameraId}/frame`),
    enabled: enabled && cameraId > 0,
    // ~5 FPS preview; offset theo id để các ô không poll cùng lúc
    refetchInterval: 200 + (cameraId % 4) * 40,
    staleTime: 150,
    retry: false,
  });
}

export function useRecentAlerts(limit = 50) {
  return useQuery({
    queryKey: ["alerts", limit],
    queryFn: () => get<AlertEvent[]>("/realtime/alerts", { limit }),
    refetchInterval: 8000,
  });
}

export function useConnections() {
  return useQuery({
    queryKey: ["connections"],
    queryFn: () => get<{ active: number; total: number }>("/realtime/connections"),
    refetchInterval: 5000,
  });
}

// ----- Rules CRUD -----
export function useRules() {
  return useQuery({
    queryKey: ["rules"],
    queryFn: () => get<Rule[]>("/rules"),
  });
}

export function useRuleStatistics() {
  return useQuery({
    queryKey: ["rules", "statistics"],
    queryFn: () => get<Record<string, unknown>>("/rules/statistics"),
    refetchInterval: 10000,
  });
}

export interface RulePayload {
  id: string;
  name?: string;
  description?: string;
  enabled: boolean;
  severity: string;
  priority: number;
  cooldown?: number | null;
  actions: string[];
  conditions: unknown[] | Record<string, unknown>;
}

export function useCreateRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: RulePayload) =>
      apiClient.post("/rules", payload).then((r) => unwrap<Rule>(r.data)),
    onSuccess: (rule) => {
      logAction("rule_change", `create ${rule.id}`);
      qc.invalidateQueries({ queryKey: ["rules"] });
    },
  });
}

export function useUpdateRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...payload }: RulePayload) =>
      apiClient.put(`/rules/${id}`, payload).then((r) => unwrap<Rule>(r.data)),
    onSuccess: (rule) => {
      logAction("rule_change", `update ${rule.id}`);
      qc.invalidateQueries({ queryKey: ["rules"] });
    },
  });
}

export function useDeleteRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/rules/${id}`),
    onSuccess: (_res, id) => {
      logAction("rule_change", `delete ${id}`);
      qc.invalidateQueries({ queryKey: ["rules"] });
    },
  });
}

export function useToggleRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, enabled }: { id: string; enabled: boolean }) =>
      apiClient
        .post(`/rules/${enabled ? "enable" : "disable"}`, { rule_id: id })
        .then((r) => unwrap<Rule>(r.data)),
    onSuccess: (rule) => {
      logAction("rule_change", `${rule.enabled ? "enable" : "disable"} ${rule.id}`);
      qc.invalidateQueries({ queryKey: ["rules"] });
    },
  });
}

// ----- Events (Sprint 7 processed events) -----
export function useEvents(limit = 100) {
  return useQuery({
    queryKey: ["events", limit],
    queryFn: () => get<AlertEvent[]>("/processing/events", { limit }),
    refetchInterval: 8000,
  });
}

// ----- Employees (fallback demo nếu backend là skeleton) -----
const DEMO_EMPLOYEES: Employee[] = [
  { id: "e1", name: "Nguyễn Văn A", department: "Sales", track_ids: [12], performance_score: 88, working_time: 25200, violation_time: 640 },
  { id: "e2", name: "Trần Thị B", department: "Support", track_ids: [15], performance_score: 72, working_time: 24100, violation_time: 1820 },
  { id: "e3", name: "Lê Văn C", department: "Dev", track_ids: [7], performance_score: 95, working_time: 26800, violation_time: 120 },
  { id: "e4", name: "Phạm Thị D", department: "HR", track_ids: [21], performance_score: 64, violation_time: 2600, working_time: 22800 },
];

export function useEmployees() {
  return useQuery({
    queryKey: ["employees"],
    queryFn: async () => {
      try {
        const res = await apiClient.get("/employees");
        const data = unwrap<Employee[]>(res.data);
        if (Array.isArray(data) && data.length) return data;
      } catch {
        /* fallback */
      }
      return DEMO_EMPLOYEES;
    },
  });
}
