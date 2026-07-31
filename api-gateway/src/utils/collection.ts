export const COLLECTION_HEADER = "x-rag-collection";
export const COLLECTION_DEFAULT = "default";
export const COLLECTION_PORTFOLIO = "portfolio";

const ALLOWED = new Set([COLLECTION_DEFAULT, COLLECTION_PORTFOLIO]);

export function normalizeCollection(value: unknown): string {
  if (typeof value !== "string" || !value.trim()) {
    return COLLECTION_DEFAULT;
  }
  const normalized = value.trim().toLowerCase();
  return ALLOWED.has(normalized) ? normalized : COLLECTION_DEFAULT;
}

export function readCollectionHeader(
  headers: Record<string, unknown> | undefined
): string {
  if (!headers) {
    return COLLECTION_DEFAULT;
  }
  const raw =
    headers[COLLECTION_HEADER] ??
    headers["X-RAG-Collection"] ??
    headers["X-Rag-Collection"];
  if (Array.isArray(raw)) {
    return normalizeCollection(raw[0]);
  }
  return normalizeCollection(raw);
}
