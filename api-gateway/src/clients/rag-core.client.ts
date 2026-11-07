import { InvokeCommand, LambdaClient } from "@aws-sdk/client-lambda";
import axios from "axios";
import FormData from "form-data";

import { env } from "../config/env";
import {
  DocumentIngestResponseBody,
  StagedDocumentBody,
} from "../types/documents.types";
import { SearchResponseBody } from "../types/search.types";
import { signRequest } from "../utils/aws-request-signer";
import {
  COLLECTION_DEFAULT,
  COLLECTION_HEADER,
} from "../utils/collection";
import { buildLambdaUrlEvent } from "../utils/lambda-url-event";

const ragCoreBaseUrl = new URL(env.RAG_CORE_URL);

const httpClient = axios.create({
  baseURL: env.RAG_CORE_URL,
});

// Only constructed lazily (inside ingestDocumentAsync) in practice, but a
// single client instance is reused across invocations/requests.
const lambdaClient = new LambdaClient({ region: env.AWS_REGION });

async function search(
  question: string,
  collection: string = COLLECTION_DEFAULT
): Promise<SearchResponseBody> {
  const path = "/api/v1/search";
  const body = JSON.stringify({ question });

  const signed = signRequest({
    host: ragCoreBaseUrl.host,
    path,
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      [COLLECTION_HEADER]: collection,
    },
    body,
  });

  const response = await httpClient.post<SearchResponseBody>(path, body, {
    headers: signed.headers,
  });

  return response.data;
}

async function startWarmup(
  collection: string = COLLECTION_DEFAULT
): Promise<void> {
  const path = "/api/v1/warmup";
  const headers = { [COLLECTION_HEADER]: collection };

  if (!env.RAG_CORE_FUNCTION_NAME) {
    const signed = signRequest({
      host: ragCoreBaseUrl.host,
      path,
      method: "POST",
      headers,
    });
    await httpClient.post(path, undefined, { headers: signed.headers });
    return;
  }

  const event = buildLambdaUrlEvent({
    method: "POST",
    path,
    headers,
    body: Buffer.alloc(0),
  });

  await lambdaClient.send(
    new InvokeCommand({
      FunctionName: env.RAG_CORE_FUNCTION_NAME,
      InvocationType: "Event",
      Payload: Buffer.from(JSON.stringify(event)),
    })
  );
}

async function getWarmupStatus(
  collection: string = COLLECTION_DEFAULT
): Promise<{ statusCode: number; data: { status: string } }> {
  const path = "/api/v1/warmup";
  const signed = signRequest({
    host: ragCoreBaseUrl.host,
    path,
    method: "GET",
    headers: { [COLLECTION_HEADER]: collection },
  });

  const response = await httpClient.get<{ status: string }>(path, {
    headers: signed.headers,
  });
  return { statusCode: response.status, data: response.data };
}

async function ingestDocument(
  file: Express.Multer.File,
  collection: string = COLLECTION_DEFAULT
): Promise<DocumentIngestResponseBody> {
  const path = "/api/v1/documents/ingest";

  const formData = new FormData();
  formData.append("file", file.buffer, {
    filename: file.originalname,
    contentType: file.mimetype,
  });

  const body = formData.getBuffer();
  const headers = {
    ...formData.getHeaders(),
    [COLLECTION_HEADER]: collection,
  };

  const signed = signRequest({
    host: ragCoreBaseUrl.host,
    path,
    method: "POST",
    headers,
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
 * The PDF is staged in private S3 first, so this event only carries a small
 * object reference and remains safely below Lambda Event's 1 MB limit. The
 * payload still looks like a Function URL event for the Lambda Web Adapter.
 */
async function ingestStagedDocumentAsync(
  staged: StagedDocumentBody,
  collection: string = COLLECTION_DEFAULT
): Promise<void> {
  const path = "/api/v1/documents/ingest-staged";
  const body = Buffer.from(JSON.stringify(staged));
  const headers = {
    "content-type": "application/json",
    [COLLECTION_HEADER]: collection,
  };

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
  documentId: string,
  collection: string = COLLECTION_DEFAULT
): Promise<DocumentIngestResponseBody> {
  const path = `/api/v1/documents/status/${encodeURIComponent(documentId)}`;

  const signed = signRequest({
    host: ragCoreBaseUrl.host,
    path,
    method: "GET",
    headers: { [COLLECTION_HEADER]: collection },
  });

  const response = await httpClient.get<DocumentIngestResponseBody>(path, {
    headers: signed.headers,
  });

  return response.data;
}

export const ragCoreClient = {
  search,
  startWarmup,
  getWarmupStatus,
  ingestDocument,
  ingestStagedDocumentAsync,
  getIngestStatus,
};
