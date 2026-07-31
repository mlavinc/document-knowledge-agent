import { createHttpClient } from "@rag-agent/ui-shared";

const API_GATEWAY_URL =
  import.meta.env.VITE_API_GATEWAY_URL ?? "http://localhost:3000";

/** Portfolio corpus only — never hits the demo vector table. */
export const httpClient = createHttpClient(API_GATEWAY_URL, {
  "X-RAG-Collection": "portfolio",
});
