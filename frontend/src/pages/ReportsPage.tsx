import { useMemo } from "react";
import { toast } from "sonner";
import { FileSpreadsheet, FileText, FileDown } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/common/DataTable";
import { useRecentAlerts } from "@/hooks/api";
import { exportCSV, exportExcel, exportPDF, type Row } from "@/lib/export";
import { logAction } from "@/lib/logger";
import { formatDateTime, formatDuration } from "@/lib/utils";
import type { AlertEvent } from "@/types";

/** Reports — xuất báo cáo Excel / PDF / CSV. */
export function ReportsPage() {
  const { data: alerts } = useRecentAlerts(200);

  const rows = useMemo<Row[]>(
    () =>
      (alerts ?? []).map((a: AlertEvent) => ({
        event_id: a.event_id,
        rule: a.rule_id,
        severity: a.severity,
        camera: a.camera_name ?? `#${a.camera_id}`,
        track: a.track_id,
        confidence: `${(a.confidence * 100).toFixed(0)}%`,
        duration: formatDuration(a.duration),
        time: formatDateTime(a.ts),
      })),
    [alerts]
  );

  const doExport = (fn: () => void, label: string) => {
    fn();
    logAction("download", `report ${label}`);
    toast.success(`Đã xuất ${label}`);
  };

  const columns: Column<Row>[] = [
    { key: "rule", header: "Rule" },
    { key: "severity", header: "Severity" },
    { key: "camera", header: "Camera" },
    { key: "track", header: "Track" },
    { key: "confidence", header: "Confidence" },
    { key: "time", header: "Time" },
  ];

  return (
    <div className="space-y-4">
      <PageHeader
        title="Reports"
        description="Xuất báo cáo vi phạm nhiều định dạng"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => doExport(() => exportExcel(rows, "aems_report.xlsx"), "Excel")}>
              <FileSpreadsheet className="h-4 w-4" /> Excel
            </Button>
            <Button variant="outline" onClick={() => doExport(() => exportPDF(rows, "aems_report.pdf", "AEMS - Báo cáo vi phạm"), "PDF")}>
              <FileText className="h-4 w-4" /> PDF
            </Button>
            <Button variant="outline" onClick={() => doExport(() => exportCSV(rows, "aems_report.csv"), "CSV")}>
              <FileDown className="h-4 w-4" /> CSV
            </Button>
          </div>
        }
      />
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold">Xem trước ({rows.length} bản ghi)</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} rows={rows} rowKey={(_r, i) => String(i)} />
        </CardContent>
      </Card>
    </div>
  );
}
