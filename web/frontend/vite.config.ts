import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api/run-excel": {
        target: "http://localhost:8081",
        changeOrigin: true,
        rewrite: () => "/",
      },
      "/api/run-json": {
        target: "http://localhost:8082",
        changeOrigin: true,
        rewrite: () => "/",
      },
      "/api/compare-scenarios": {
        target: "http://localhost:8083",
        changeOrigin: true,
        rewrite: () => "/",
      },
      "/api/run-sensitivity": {
        target: "http://localhost:8084",
        changeOrigin: true,
        rewrite: () => "/",
      },
    },
  },
});
