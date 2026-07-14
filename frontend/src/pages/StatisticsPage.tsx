import { useMemo, useState } from "react";
import { PageHeader } from "@/components/common/PageHeader";
import {
  AreaChartCard,
  BarChartCard,
  LineChartCard,
  PieChartCard,
} from "@/components/charts/Charts";
import { HeatmapChart, type HeatPoint } from "@/components/charts/HeatmapChart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useRecentAlerts } from "@/hooks/api";

const PERIODS = [
  { value: "day", label: "Theo ngày" },
  { value: "week", label: "Theo tuần" },
  { value: "month", label: "Theo tháng" },
];

function groupCount<T>(items: T[], key: (t: T) => string) {
  const m: Record<string, number> = {};
  items.forEach((i) => {
    const k = key(i);
    m[k] = (m[k] ?? 0) + 1;
  });
  return Object.entries(m).map(([name, value]) => ({ name, value }));
}

/** Statistics — thống kê theo ngày/tuần/tháng/camera/rule + biểu đồ Recharts. */
export function StatisticsPage() {
  const { data: alerts } = useRecentAlerts(200);
  const [period, setPeriod] = useState("day");
  const [rule, setRule] = useState("all");

  const items = useMemo(() => {
    const a = alerts ?? [];
    return rule === "all" ? a : a.filter((x) => x.rule_id === rule);
  }, [alerts, rule]);

  const byRule = useMemo(() => groupCount(items, (a) => a.rule_id), [items]);
  const bySeverity = useMemo(() => groupCount(items, (a) => a.severity), [items]);
  const byCamera = useMemo(
    () => groupCount(items, (a) => a.camera_name ?? `Cam ${a.camera_id}`),
    [items]
  );
  const overTime = useMemo(() => {
    const buckets: Record<string, number> = {};
    items.forEach((a) => {
      const h = new Date(a.ts ?? Date.now()).getHours();
      const k = `${h}:00`;
      buckets[k] = (buckets[k] ?? 0) + 1;
    });
    return Object.entries(buckets)
      .map(([name, value]) => ({ name, value }))
      .sort((x, y) => parseInt(x.name) - parseInt(y.name));
  }, [items]);

  const ruleOptions = useMemo(
    () => ["all", ...new Set((alerts ?? []).map((a) => a.rule_id))],
    [alerts]
  );

  // Điểm nóng hành vi: ánh xạ track/camera → toạ độ ổn định (demo)
  const heatPoints = useMemo<HeatPoint[]>(
    () =>
      items.map((a) => {
        const seed = (a.track_id * 97 + a.camera_id * 31) % 100;
        return {
          x: 0.1 + ((seed % 10) / 10) * 0.8,
          y: 0.1 + (Math.floor(seed / 10) / 10) * 0.8,
          weight: Math.min(1, a.confidence + 0.2),
        };
      }),
    [items]
  );

  return (
    <div className="space-y-4">
      <PageHeader
        title="Statistics"
        description="Phân tích vi phạm theo thời gian, camera và rule"
        actions={
          <div className="flex gap-2">
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PERIODS.map((p) => (
                  <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={rule} onValueChange={setRule}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ruleOptions.map((r) => (
                  <SelectItem key={r} value={r}>{r === "all" ? "Tất cả rule" : r}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <BarChartCard title="Vi phạm theo Rule" data={byRule} xKey="name" yKey="value" />
        <PieChartCard title="Phân bố theo Severity" data={bySeverity} nameKey="name" valueKey="value" />
        <AreaChartCard title="Vi phạm theo giờ" data={overTime} xKey="name" yKey="value" />
        <LineChartCard title="Vi phạm theo Camera" data={byCamera} xKey="name" yKey="value" />
      </div>

      <HeatmapChart title="Heatmap điểm nóng hành vi (Phone / Talking / Eating / Sleeping / Away)" points={heatPoints} />
    </div>
  );
}
