import axios from "axios";
import FormData from "form-data";

import { env } from "../config/env";
import { DocumentIngestResponseBody } from "../types/documents.types";
import { SearchResponseBody } from "../types/search.types";
import { signRequest } from "../utils/aws-request-signer";

const ragCoreBaseUrl = new URL(env.RAG_CORE_URL);

const httpClient = axios.create({
  baseURL: env.RAG_CORE_URL,
});

async function search(question: string): Promise<SearchResponseBody> {
  const path = "/api/v1/search";
  const body = JSON.stringify({ question });

  const signed = signRequest({
    host: ragCoreBaseUrl.host,
    path,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });

  const response = await httpClient.post<SearchResponseBody>(path, body, {
    headers: signed.headers,
  });

  return response.data;
}

async function ingestDocument(
  file: Express.Multer.File
): Promise<DocumentIngestResponseBody> {
  const path = "/api/v1/documents/ingest";

  const formData = new FormData();
  formData.append("file", file.buffer, {
    filename: file.originalname,
    contentType: file.mimetype,
  });

  const body = formData.getBuffer();

  const signed = signRequest({
    host: ragCoreBaseUrl.host,
    path,
    method: "POST",
    headers: formData.getHeaders(),
    body,
  });

  const response = await httpClient.post<DocumentIngestResponseBody>(
    path,
    body,
    { headers: signed.headers }
  );

  return response.data;
}

export const ragCoreClient = {
  search,
  ingestDocument,
};
