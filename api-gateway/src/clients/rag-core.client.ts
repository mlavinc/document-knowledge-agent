import { InvokeCommand, LambdaClient } from "@aws-sdk/client-lambda";
import axios from "axios";
import FormData from "form-data";

import { env } from "../config/env";
import { DocumentIngestResponseBody } from "../types/documents.types";
import { SearchResponseBody } from "../types/search.types";
import { signRequest } from "../utils/aws-request-signer";
import { buildLambdaUrlEvent } from "../utils/lambda-url-event";

const ragCoreBaseUrl = new URL(env.RAG_CORE_URL);

const httpClient = axios.create({
  baseURL: env.RAG_CORE_URL,
});

// Only constructed lazily (inside ingestDocumentAsync) in practice, but a
// single client instance is reused across invocations/requests.
const lambdaClient = new LambdaClient({ region: env.AWS_REGION });

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

/**
 * Fire-and-forget ingestion: invokes rag-core's Lambda function directly
 * and asynchronously (InvocationType="Event"), bypassing HTTP entirely.
 * AWS Lambda queues the invocation and returns immediately (no wait on
 * rag-core actually finishing), which is what allows this call to
 * complete well within API Gateway's ~29s hard timeout regardless of how
 * long the underlying ingestion pipeline takes (up to rag-core's own
 * Lambda timeout, run in a separate execution environment).
 *
 * rag-core's FastAPI endpoint and its Lambda Web Adapter setup are
 * unchanged: the adapter only knows how to translate API Gateway/ALB/
 * Function URL-shaped events into HTTP requests, so the payload here is
 * built to look exactly like a real Function URL invocation event.
 */
async function ingestDocumentAsync(
  file: Express.Multer.File
): Promise<void> {
  const path = "/api/v1/documents/ingest";

  const formData = new FormData();
  formData.append("file", file.buffer, {
    filename: file.originalname,
    contentType: file.mimetype,
  });

  const body = formData.getBuffer();
  const headers = formData.getHeaders();

  const event = buildLambdaUrlEvent({
    method: "POST",
    path,
    headers,
    body,
  });

  await lambdaClient.send(
    new InvokeCommand({
      FunctionName: env.RAG_CORE_FUNCTION_NAME,
      InvocationType: "Event",
      Payload: Buffer.from(JSON.stringify(event)),
    })
  );
}

async function getIngestStatus(
  documentId: string
): Promise<DocumentIngestResponseBody> {
  const path = `/api/v1/documents/status/${encodeURIComponent(documentId)}`;

  const signed = signRequest({
    host: ragCoreBaseUrl.host,
    path,
    method: "GET",
    headers: {},
  });

  const response = await httpClient.get<DocumentIngestResponseBody>(path, {
    headers: signed.headers,
  });

  return response.data;
}

export const ragCoreClient = {
  search,
  ingestDocument,
  ingestDocumentAsync,
  getIngestStatus,
};
