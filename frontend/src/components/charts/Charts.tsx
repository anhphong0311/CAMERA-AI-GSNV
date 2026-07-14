import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export const CHART_COLORS = [
  "#3b82f6",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#06b6d4",
  "#ec4899",
];

interface Datum {
  [key: string]: string | number;
}

function ChartCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {children as React.ReactElement}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

const tooltipStyle = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: 8,
  fontSize: 12,
  color: "hsl(var(--popover-foreground))",
};

export function BarChartCard({
  title,
  data,
  xKey,
  yKey,
}: {
  title: string;
  data: Datum[];
  xKey: string;
  yKey: string;
}) {
  return (
    <ChartCard title={title}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
        <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
        <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "hsl(var(--muted))" }} />
        <Bar dataKey={yKey} radius={[4, 4, 0, 0]} fill={CHART_COLORS[0]} />
      </BarChart>
    </ChartCard>
  );
}

export function LineChartCard({
  title,
  data,
  xKey,
  yKey,
}: {
  title: string;
  data: Datum[];
  xKey: string;
  yKey: string;
}) {
  return (
    <ChartCard title={title}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
        <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
        <Tooltip contentStyle={tooltipStyle} />
        <Line type="monotone" dataKey={yKey} stroke={CHART_COLORS[1]} strokeWidth={2} dot={false} />
      </LineChart>
    </ChartCard>
  );
}

export function AreaChartCard({
  title,
  data,
  xKey,
  yKey,
}: {
  title: string;
  data: Datum[];
  xKey: string;
  yKey: string;
}) {
  return (
    <ChartCard title={title}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={CHART_COLORS[0]} stopOpacity={0.5} />
            <stop offset="95%" stopColor={CHART_COLORS[0]} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
        <XAxis dataKey={xKey} tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
        <YAxis tick={{ fontSize: 11 }} stroke="hsl(var(--muted-foreground))" />
        <Tooltip contentStyle={tooltipStyle} />
        <Area type="monotone" dataKey={yKey} stroke={CHART_COLORS[0]} fill="url(#areaFill)" strokeWidth={2} />
      </AreaChart>
    </ChartCard>
  );
}

export function PieChartCard({
  title,
  data,
  nameKey,
  valueKey,
}: {
  title: string;
  data: Datum[];
  nameKey: string;
  valueKey: string;
}) {
  return (
    <ChartCard title={title}>
      <PieChart>
        <Tooltip contentStyle={tooltipStyle} />
        <Pie
          data={data}
          dataKey={valueKey}
          nameKey={nameKey}
          cx="50%"
          cy="50%"
          outerRadius={90}
          label={{ fontSize: 11 }}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
      </PieChart>
    </ChartCard>
  );
}
