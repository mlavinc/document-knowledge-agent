export interface DocumentIngestResponseBody {
  filename: string;
  chunks: number;
  status: string;
}

/**
 * Immediate acknowledgment returned in INGESTION_MODE="async": rag-core
 * has been triggered but has not necessarily finished (or even started)
 * processing the document yet.
 */
export interface DocumentIngestAcceptedBody {
  document_id: string;
  filename: string;
  status: "processing";
}
