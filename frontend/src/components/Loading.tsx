import { Loader2 } from "lucide-react";

/**
 * Component loading toàn màn hình — hiển thị khi lazy load route hoặc fetch data.
 */
export function Loading() {
  return (
    <div className="flex min-h-[200px] flex-col items-center justify-center gap-3 text-muted-foreground">
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
      <p className="text-sm">Đang tải...</p>
    </div>
  );
}
