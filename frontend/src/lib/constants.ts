import {
  LayoutDashboard,
  Video,
  Camera,
  ScanEye,
  Radar,
  AlertTriangle,
  PlayCircle,
  Users,
  ListChecks,
  PencilRuler,
  BarChart3,
  FileText,
  Settings,
  Activity,
  ScrollText,
  Brain,
  type LucideIcon,
} from "lucide-react";
import type { Role } from "@/types";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  roles?: Role[]; // undefined = mọi role
}

/** Menu chính của Dashboard (theo spec Sprint 8). */
export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/live", label: "Live Camera", icon: Video },
  { to: "/cameras", label: "Camera Management", icon: Camera, roles: ["admin", "supervisor"] },
  { to: "/detection", label: "Live Detection", icon: ScanEye },
  { to: "/tracking", label: "Tracking", icon: Radar },
  { to: "/alerts", label: "Alerts", icon: AlertTriangle },
  { to: "/replay", label: "Replay", icon: PlayCircle },
  { to: "/employees", label: "Employees", icon: Users, roles: ["admin", "supervisor"] },
  { to: "/rules", label: "Rules", icon: ListChecks, roles: ["admin", "supervisor"] },
  { to: "/roi", label: "ROI Editor", icon: PencilRuler, roles: ["admin", "supervisor"] },
  { to: "/statistics", label: "Statistics", icon: BarChart3 },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/training", label: "AI Training", icon: Brain, roles: ["admin", "supervisor"] },
  { to: "/settings", label: "Settings", icon: Settings, roles: ["admin"] },
  { to: "/system", label: "System Monitor", icon: Activity },
  { to: "/logs", label: "Logs", icon: ScrollText, roles: ["admin", "supervisor"] },
];

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Admin",
  supervisor: "Supervisor",
  viewer: "Viewer",
};

export const DETECTION_LABELS = [
  "person",
  "phone",
  "bottle",
  "food",
  "cup",
  "monitor",
  "laptop",
  "keyboard",
] as const;

export const GRID_OPTIONS = [1, 4, 9, 16] as const;
