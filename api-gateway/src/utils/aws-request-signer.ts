import aws4 from "aws4";

import { env } from "../config/env";

export interface SignableRequest {
  host: string;
  path: string;
  method: string;
  headers: Record<string, string>;
  body?: string | Buffer;
}

/**
 * Signs an outgoing request with SigV4 when RAG_CORE_AUTH_MODE=iam
 * (production, calling a Lambda Function URL with IAM auth). In local
 * development (RAG_CORE_AUTH_MODE=none) this is a no-op, so rag-core.client
 * never needs to know which mode is active.
 */
export function signRequest(request: SignableRequest): SignableRequest {
  if (env.RAG_CORE_AUTH_MODE !== "iam") {
    return request;
  }

  const signed = aws4.sign(
    {
      host: request.host,
      path: request.path,
      method: request.method,
      headers: request.headers,
      body: request.body,
      service: "lambda",
      region: env.AWS_REGION,
    }
    // Credentials are resolved from the Lambda execution role's
    // environment variables (AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY /
    // AWS_SESSION_TOKEN), which aws4 picks up automatically when omitted.
  );

  return {
    host: request.host,
    path: signed.path ?? request.path,
    method: request.method,
    headers: signed.headers as Record<string, string>,
    body: request.body,
  };
}
