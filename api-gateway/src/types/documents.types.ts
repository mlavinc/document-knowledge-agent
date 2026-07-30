export interface DocumentIngestResponseBody {
  filename: string;
  chunks?: number;
  status: string;
  document_id?: string;
  error?: string;
}

/**
 * Immediate acknowledgment returned in INGESTION_MODE="async": rag-core
 * has been triggered but has not necessarily finished (or even started)
 * processing the document yet. The frontend polls GET /api/documents/status/:id.
 */
export interface DocumentIngestAcceptedBody {
  document_id: string;
  filename: string;
  status: "processing";
}
