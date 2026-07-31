import { useChat } from "@rag-agent/ui-shared";

import { httpClient } from "../api/http";

/** Portfolio chat — search only; never touches document ingest APIs. */
export function usePortfolioChat() {
  return useChat(httpClient);
}
