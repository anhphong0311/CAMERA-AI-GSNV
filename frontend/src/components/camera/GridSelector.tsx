import { GRID_OPTIONS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LayoutGrid } from "lucide-react";

export type GridSize = number | "all";

/** Chọn số ô lưới hoặc hiển thị tất cả camera đang bật. */
export function GridSelector({
  value,
  onChange,
  allCount,
}: {
  value: GridSize;
  onChange: (n: GridSize) => void;
  allCount: number;
}) {
  return (
    <div className="flex items-center gap-1 rounded-md border p-1">
      <LayoutGrid className="mx-1 h-4 w-4 text-muted-foreground" />
      {GRID_OPTIONS.map((n) => (
        <Button
          key={n}
          size="sm"
          variant={value === n ? "default" : "ghost"}
          className={cn("h-7 w-9 px-0 text-xs")}
          onClick={() => onChange(n)}
        >
          {n}
        </Button>
      ))}
      <Button
        size="sm"
        variant={value === "all" ? "default" : "ghost"}
        className="h-7 px-2 text-xs"
        onClick={() => onChange("all")}
      >
        Tất cả ({allCount})
      </Button>
    </div>
  );
}
