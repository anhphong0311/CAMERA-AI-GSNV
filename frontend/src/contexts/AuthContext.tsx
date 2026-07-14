import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiClient, tokenStore, unwrap } from "@/lib/api";
import { logAction } from "@/lib/logger";
import type { AuthUser, Role } from "@/types";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (username: string, password: string, remember: boolean) => Promise<void>;
  logout: () => void;
  hasRole: (...roles: Role[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const USER_KEY = "aems.user";

function loadUser(): AuthUser | null {
  try {
    const raw =
      localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

/** Suy role demo từ username khi backend chưa trả role (fallback). */
function inferRole(username: string): Role {
  const u = username.toLowerCase();
  if (u.includes("admin")) return "admin";
  if (u.includes("super")) return "supervisor";
  return "viewer";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(loadUser);

  const persist = useCallback((u: AuthUser, remember: boolean) => {
    const store = remember ? localStorage : sessionStorage;
    store.setItem(USER_KEY, JSON.stringify(u));
    setUser(u);
  }, []);

  const login = useCallback(
    async (username: string, password: string, remember: boolean) => {
      let resolved: AuthUser | null = null;
      try {
        const res = await apiClient.post("/auth/login", {
          username,
          password,
        });
        const data = unwrap<Record<string, unknown>>(res.data);
        const access = (data.access_token ?? data.accessToken) as string | undefined;
        const refresh = (data.refresh_token ?? data.refreshToken) as string | undefined;
        if (access) tokenStore.set(access, refresh);
        const u = (data.user ?? {}) as Partial<AuthUser>;
        resolved = {
          id: String(u.id ?? username),
          username: u.username ?? username,
          role: (u.role as Role) ?? inferRole(username),
          fullName: u.fullName,
        };
      } catch {
        // Fallback demo (backend auth chưa sẵn sàng) — cho phép Dashboard chạy.
        resolved = {
          id: username,
          username,
          role: inferRole(username),
          fullName: username,
        };
      }
      persist(resolved, remember);
      logAction("login", username, username);
    },
    [persist]
  );

  const logout = useCallback(() => {
    logAction("logout", user?.username, user?.username);
    tokenStore.clear();
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(USER_KEY);
    setUser(null);
  }, [user]);

  const hasRole = useCallback(
    (...roles: Role[]) => (user ? roles.includes(user.role) : false),
    [user]
  );

  useEffect(() => {
    // Đồng bộ user giữa các tab
    const onStorage = (e: StorageEvent) => {
      if (e.key === USER_KEY) setUser(loadUser());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: !!user, login, logout, hasRole }),
    [user, login, logout, hasRole]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth phải dùng trong AuthProvider");
  return ctx;
}
