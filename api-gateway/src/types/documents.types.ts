export interface DocumentIngestResponseBody {
  filename: string;
  chunks?: number;
  suggestions?: string[];
  status: string;
  document_id?: string;
  error?: string;
}

export interface StagedDocumentBody {
  document_id: string;
  object_key: string;
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
