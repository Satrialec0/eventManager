import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // eventManager API in Docker is on 8002 (see docker-compose.yml). Host uvicorn can use the same port.
      "/api": "http://127.0.0.1:8002",
      "/docs": "http://127.0.0.1:8002",
      "/openapi.json": "http://127.0.0.1:8002",
    },
  },
});
