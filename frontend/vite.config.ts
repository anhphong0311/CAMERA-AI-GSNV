/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

/**
 * Vite configuration — React + TypeScript + path alias @/ + Vitest.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Chia vendor bundle lớn thành các file nhỏ. Trên bản chạy local qua
        // Docker/WSL, response gzip lớn đôi lúc bị ngắt giữa chừng khi F5.
        manualChunks(id) {
          if (!id.includes("node_modules")) return undefined;
          const packagePath = id.split("node_modules/")[1];
          if (!packagePath) return "vendor";
          const parts = packagePath.split("/");
          const packageName = parts[0].startsWith("@")
            ? `${parts[0]}-${parts[1] ?? "package"}`
            : parts[0];
          return `vendor-${packageName.replace(/[^a-zA-Z0-9_-]/g, "-")}`;
        },
      },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
});
