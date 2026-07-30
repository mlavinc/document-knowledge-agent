import { env } from "../config/env";
import { ragCoreClient } from "../clients/rag-core.client";
import {
  DocumentIngestAcceptedBody,
  DocumentIngestResponseBody,
} from "../types/documents.types";

async function ingest(
  file: Express.Multer.File
): Promise<DocumentIngestResponseBody> {
  return ragCoreClient.ingestDocument(file);
}

async function ingestAsync(
  file: Express.Multer.File
): Promise<DocumentIngestAcceptedBody> {
  await ragCoreClient.ingestDocumentAsync(file);

  return {
    document_id: file.originalname,
    filename: file.originalname,
    status: "processing",
  };
}

async function getStatus(
  documentId: string
): Promise<DocumentIngestResponseBody> {
  return ragCoreClient.getIngestStatus(documentId);
}

function isAsyncMode(): boolean {
  return env.INGESTION_MODE === "async";
}

export const documentsService = {
  ingest,
  ingestAsync,
  getStatus,
  isAsyncMode,
};
