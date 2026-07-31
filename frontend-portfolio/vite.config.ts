import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const rootDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@rag-agent/ui-shared": path.resolve(
        rootDir,
        "../packages/rag-ui-shared/src"
      ),
    },
  },
  server: {
    port: 5174,
  },
});
