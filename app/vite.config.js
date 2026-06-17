import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    allowedHosts: ["ttstats.duckdns.org"],
    proxy: {
      "/analyze": "http://localhost:8000",
      "/files":   "http://localhost:8000",
      "/clubs":   "http://localhost:8000",
    },
  },
});