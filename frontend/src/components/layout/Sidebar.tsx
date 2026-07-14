import { NavLink } from "react-router-dom";
import { ShieldCheck, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

/**
 * Sidebar điều hướng chính — lọc menu theo role, hỗ trợ đóng trên mobile.
 */
export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { hasRole } = useAuth();
  const items = NAV_ITEMS.filter((i) => !i.roles || hasRole(...i.roles));

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r bg-card transition-transform lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex h-16 items-center justify-between px-5">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            <div className="leading-tight">
              <p className="text-sm font-bold">AEMS</p>
              <p className="text-[10px] text-muted-foreground">Operation Center</p>
            </div>
          </div>
          <button className="lg:hidden" onClick={onClose} aria-label="Đóng menu">
            <X className="h-5 w-5" />
          </button>
        </div>
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={onClose}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground shadow-sm"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-3 text-[10px] text-muted-foreground">
          Sprint 8 · v8.0.0
        </div>
      </aside>
    </>
  );
}
