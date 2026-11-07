import { randomUUID } from "node:crypto";

import axios from "axios";

import { env } from "../config/env";
import { signS3Request } from "../utils/aws-request-signer";

function safeFilename(filename: string): string {
  return filename.replace(/[^a-zA-Z0-9._-]+/g, "_");
}

function encodeObjectPath(key: string): string {
  return `/${key.split("/").map(encodeURIComponent).join("/")}`;
}

async function signedS3Request(
  method: "PUT" | "DELETE",
  key: string,
  body?: Buffer,
  contentType?: string
): Promise<void> {
  if (!env.S3_DOCUMENTS_BUCKET) {
    throw new Error("S3_DOCUMENTS_BUCKET is required for async ingestion");
  }

  const host = `${env.S3_DOCUMENTS_BUCKET}.s3.${env.AWS_REGION}.amazonaws.com`;
  const path = encodeObjectPath(key);
  const headers: Record<string, string> = {};
  if (body) {
    headers["Content-Type"] = contentType || "application/octet-stream";
    headers["Content-Length"] = String(body.length);
  }

  const signed = signS3Request({ host, path, method, headers, body });
  await axios.request({
    url: `https://${host}${signed.path}`,
    method,
    headers: signed.headers,
    data: body,
    maxBodyLength: Infinity,
  });
}

async function stage(
  file: Express.Multer.File,
  collection: string
): Promise<{ documentId: string; objectKey: string }> {
  const documentId = file.originalname;
  const objectKey = [
    "staging",
    collection,
    `${randomUUID()}-${safeFilename(documentId)}`,
  ].join("/");

  await signedS3Request("PUT", objectKey, file.buffer, file.mimetype);
  return { documentId, objectKey };
}

async function remove(objectKey: string): Promise<void> {
  await signedS3Request("DELETE", objectKey);
}

export const stagedDocumentsService = { stage, remove };
