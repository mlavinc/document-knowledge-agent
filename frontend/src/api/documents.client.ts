import { httpClient } from "./http";
import { DocumentIngestResponseBody } from "../types/rag.types";

export async function ingestDocument(
  file: File
): Promise<DocumentIngestResponseBody> {
  const formData = new FormData();
  formData.append("file", file);

  // Do not set Content-Type manually: the browser must generate it
  // (including the multipart boundary) when sending a FormData body.
  const response = await httpClient.post<DocumentIngestResponseBody>(
    "/api/documents/ingest",
    formData
  );

  return response.data;
}

export async function getDocumentStatus(
  documentId: string
): Promise<DocumentIngestResponseBody> {
  const response = await httpClient.get<DocumentIngestResponseBody>(
    `/api/documents/status/${encodeURIComponent(documentId)}`
  );
  return response.data;
}
