import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    // Proxy API calls to FastAPI during development so you avoid CORS issues.
    // Change the target if your FastAPI runs on a different port.
    proxy: {
      "/analyze": "http://localhost:8000",
      "/jobs":    "http://localhost:8000",
      "/download":"http://localhost:8000",
      "/health":  "http://localhost:8000",
    },
  },
});
