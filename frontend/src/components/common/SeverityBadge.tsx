import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { severityColor } from "@/lib/utils";
import type { Severity } from "@/types";

/** Badge hiển thị mức độ nghiêm trọng của alert. */
export function SeverityBadge({ severity }: { severity: Severity | string }) {
  return (
    <Badge className={cn("border-transparent", severityColor(severity))}>
      {String(severity).toUpperCase()}
    </Badge>
  );
}
