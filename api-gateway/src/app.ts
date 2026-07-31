import cors from "cors";
import express from "express";
import helmet from "helmet";

import { env } from "./config/env";
import { errorMiddleware } from "./middleware/error.middleware";
import { requestLogger } from "./middleware/logger.middleware";
import documentsRoutes from "./routes/documents.routes";
import healthRoutes from "./routes/health.routes";
import searchRoutes from "./routes/search.routes";

const app = express();

function resolveCorsOrigin(): boolean | string | string[] {
  const raw = env.CORS_ORIGIN.trim();
  if (!raw || raw === "*") {
    return true;
  }
  const origins = raw
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
  if (origins.length === 0) {
    return true;
  }
  if (origins.length === 1) {
    return origins[0] as string;
  }
  return origins;
}

app.use(helmet());
app.use(
  cors({
    origin: resolveCorsOrigin(),
    allowedHeaders: ["Content-Type", "X-RAG-Collection"],
  })
);
app.use(express.json());
app.use(requestLogger);

app.use(healthRoutes);
app.use(searchRoutes);
app.use(documentsRoutes);

app.use(errorMiddleware);

export default app;
