import axios, {
  AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

/**
 * Axios client + interceptor JWT.
 *
 * - Gắn Bearer access token từ localStorage.
 * - Tự refresh khi 401 (một lần) rồi retry request.
 * - Dashboard chỉ gọi API — không xử lý business logic.
 */

const ACCESS_KEY = "aems.accessToken";
const REFRESH_KEY = "aems.refreshToken";

export const tokenStore = {
  get access(): string | null {
    return localStorage.getItem(ACCESS_KEY);
  },
  get refresh(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  set(access: string, refresh?: string) {
    localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStore.access;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function doRefresh(): Promise<string | null> {
  const refresh = tokenStore.refresh;
  if (!refresh) return null;
  try {
    const res = await axios.post(
      `${apiClient.defaults.baseURL}/auth/refresh`,
      { refresh_token: refresh },
      { headers: { "Content-Type": "application/json" } }
    );
    const data = res.data?.data ?? res.data;
    const access = data?.access_token ?? data?.accessToken;
    if (access) {
      tokenStore.set(access, data?.refresh_token ?? data?.refreshToken);
      return access;
    }
  } catch {
    /* ignore */
  }
  return null;
}

apiClient.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      refreshing = refreshing ?? doRefresh();
      const newAccess = await refreshing;
      refreshing = null;
      if (newAccess) {
        original.headers.Authorization = `Bearer ${newAccess}`;
        return apiClient(original);
      }
      tokenStore.clear();
      if (!location.pathname.startsWith("/login")) {
        location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

/** Helper: unwrap ApiResponse { data } của backend AEMS. */
export function unwrap<T>(payload: { data: T } | T): T {
  if (payload && typeof payload === "object" && "data" in payload) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}
