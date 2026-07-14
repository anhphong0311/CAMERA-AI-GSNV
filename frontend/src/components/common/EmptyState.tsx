import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

/**
 * Trạng thái rỗng — dùng khi danh sách chưa có dữ liệu.
 */
export function EmptyState({
  icon: Icon = Inbox,
  title = "Chưa có dữ liệu",
  description,
}: {
  icon?: LucideIcon;
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center text-muted-foreground">
      <Icon className="h-10 w-10 opacity-40" />
      <p className="font-medium">{title}</p>
      {description && <p className="text-sm">{description}</p>}
    </div>
  );
}
