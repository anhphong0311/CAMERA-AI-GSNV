import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Trash2, FileDown } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { DataTable, type Column } from "@/components/common/DataTable";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { clearActionLogs, getActionLogs, type ActionLog } from "@/lib/logger";
import { exportCSV } from "@/lib/export";
import { formatDateTime } from "@/lib/utils";

const ACTIONS = [
  "all",
  "login",
  "logout",
  "view_camera",
  "replay",
  "download",
  "rule_change",
  "roi_change",
  "settings_change",
];

/** Logs — nhật ký hành động người dùng (login, view camera, replay, download, rule change). */
export function LogsPage() {
  const [filter, setFilter] = useState("all");
  const [logs, setLogs] = useState<ActionLog[]>(getActionLogs());

  const rows = useMemo(
    () => (filter === "all" ? logs : logs.filter((l) => l.action === filter)),
    [logs, filter]
  );

  const columns: Column<ActionLog>[] = [
    { key: "action", header: "Hành động", render: (r) => <Badge variant="secondary">{r.action}</Badge> },
    { key: "detail", header: "Chi tiết", render: (r) => r.detail ?? "—" },
    { key: "user", header: "Người dùng", render: (r) => r.user ?? "—" },
    { key: "ts", header: "Thời gian", render: (r) => formatDateTime(r.ts) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Logs"
        description="Nhật ký hoạt động người dùng"
        actions={
          <div className="flex gap-2">
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-44">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ACTIONS.map((a) => (
                  <SelectItem key={a} value={a}>{a === "all" ? "Tất cả" : a}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => exportCSV(rows as unknown as Record<string, string>[], "logs.csv")}
            >
              <FileDown className="h-4 w-4" /> CSV
            </Button>
            <Button
              variant="ghost"
              className="text-destructive"
              onClick={() => {
                clearActionLogs();
                setLogs([]);
                toast.success("Đã xoá nhật ký");
              }}
            >
              <Trash2 className="h-4 w-4" /> Xoá
            </Button>
          </div>
        }
      />
      <Card>
        <CardContent className="pt-4">
          <DataTable columns={columns} rows={rows} rowKey={(_r, i) => String(i)} emptyMessage="Chưa có nhật ký" />
        </CardContent>
      </Card>
    </div>
  );
}
