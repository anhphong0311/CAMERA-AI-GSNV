import { GRID_OPTIONS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { LayoutGrid } from "lucide-react";

/** Chọn số ô lưới hiển thị camera (1/4/9/16). */
export function GridSelector({
  value,
  onChange,
}: {
  value: number;
  onChange: (n: number) => void;
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
    </div>
  );
}
