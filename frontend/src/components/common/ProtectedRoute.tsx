import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import type { Role } from "@/types";

/**
 * Guard route — yêu cầu đăng nhập; tùy chọn giới hạn theo role.
 */
export function ProtectedRoute({ roles }: { roles?: Role[] }) {
  const { isAuthenticated, hasRole } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (roles && roles.length > 0 && !hasRole(...roles)) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
