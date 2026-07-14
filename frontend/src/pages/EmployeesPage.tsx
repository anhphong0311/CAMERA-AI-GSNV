import { useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { DataTable, type Column } from "@/components/common/DataTable";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useEmployees } from "@/hooks/api";
import { formatDuration } from "@/lib/utils";
import type { Employee } from "@/types";

function scoreVariant(score = 0) {
  if (score >= 85) return "success" as const;
  if (score >= 70) return "warning" as const;
  return "destructive" as const;
}

/** Employee — hiệu suất, thời gian làm việc, thời gian vi phạm. */
export function EmployeesPage() {
  const { data } = useEmployees();
  const [selected, setSelected] = useState<Employee | null>(null);

  const columns: Column<Employee>[] = [
    { key: "name", header: "Nhân viên", render: (r) => <span className="font-medium">{r.name}</span> },
    { key: "department", header: "Phòng ban", render: (r) => r.department ?? "—" },
    {
      key: "performance_score",
      header: "Performance",
      render: (r) => (
        <div className="flex items-center gap-2">
          <Progress value={r.performance_score ?? 0} className="w-24" />
          <Badge variant={scoreVariant(r.performance_score)}>{r.performance_score ?? 0}</Badge>
        </div>
      ),
    },
    { key: "working_time", header: "Working Time", render: (r) => formatDuration(r.working_time) },
    { key: "violation_time", header: "Violation Time", render: (r) => formatDuration(r.violation_time) },
  ];

  return (
    <div className="space-y-4">
      <PageHeader title="Employees" description="Danh sách nhân viên & hiệu suất giám sát" />
      <Card>
        <CardContent className="pt-4">
          <DataTable columns={columns} rows={data ?? []} rowKey={(r) => r.id} onRowClick={setSelected} />
        </CardContent>
      </Card>

      <Dialog open={!!selected} onOpenChange={(v) => !v && setSelected(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selected?.name}</DialogTitle>
          </DialogHeader>
          {selected && (
            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3">
                <Stat label="Performance Score" value={String(selected.performance_score ?? "—")} />
                <Stat label="Phòng ban" value={selected.department ?? "—"} />
                <Stat label="Working Time" value={formatDuration(selected.working_time)} />
                <Stat label="Violation Time" value={formatDuration(selected.violation_time)} />
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">Track History</p>
                <div className="flex flex-wrap gap-1">
                  {(selected.track_ids ?? []).map((t) => (
                    <Badge key={t} variant="secondary">#{t}</Badge>
                  ))}
                  {(selected.track_ids ?? []).length === 0 && <span>—</span>}
                </div>
              </div>
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">Event History</p>
                <p className="text-muted-foreground">
                  Lịch sử sự kiện được liên kết qua Track ID trong module Alert.
                </p>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}
