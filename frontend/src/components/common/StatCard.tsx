import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

/**
 * Thẻ chỉ số (KPI) dùng ở Overview / System Monitor.
 */
export function StatCard({
  title,
  value,
  icon: Icon,
  hint,
  accent = "text-primary",
}: {
  title: string;
  value: ReactNode;
  icon: LucideIcon;
  hint?: string;
  accent?: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between p-5">
        <div className="space-y-1">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {title}
          </p>
          <p className="text-2xl font-bold">{value}</p>
          {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
        </div>
        <div className={cn("rounded-lg bg-muted p-3", accent)}>
          <Icon className="h-6 w-6" />
        </div>
      </CardContent>
    </Card>
  );
}
