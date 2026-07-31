import { env } from "../config/env";
import { ragCoreClient } from "../clients/rag-core.client";
import {
  DocumentIngestAcceptedBody,
  DocumentIngestResponseBody,
} from "../types/documents.types";
import { COLLECTION_DEFAULT } from "../utils/collection";

async function ingest(
  file: Express.Multer.File,
  collection: string = COLLECTION_DEFAULT
): Promise<DocumentIngestResponseBody> {
  return ragCoreClient.ingestDocument(file, collection);
}

async function ingestAsync(
  file: Express.Multer.File,
  collection: string = COLLECTION_DEFAULT
): Promise<DocumentIngestAcceptedBody> {
  await ragCoreClient.ingestDocumentAsync(file, collection);

  return {
    document_id: file.originalname,
    filename: file.originalname,
    status: "processing",
  };
}

async function getStatus(
  documentId: string,
  collection: string = COLLECTION_DEFAULT
): Promise<DocumentIngestResponseBody> {
  return ragCoreClient.getIngestStatus(documentId, collection);
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
