/**
 * Builds a payload matching the JSON shape AWS generates for a Lambda
 * Function URL invocation (payload format 2.0), so that it can be sent
 * as the raw `Payload` of a direct `lambda:Invoke` call and still be
 * understood by the Lambda Web Adapter running inside rag-core (which
 * only knows how to translate this shape — or API Gateway/ALB events —
 * into an HTTP request to the local FastAPI server).
 *
 * This lets us invoke rag-core asynchronously (InvocationType="Event")
 * while reusing its existing HTTP endpoint untouched.
 */
export interface LambdaUrlEventInput {
  method: string;
  path: string;
  headers: Record<string, string>;
  body: Buffer;
}

export function buildLambdaUrlEvent(input: LambdaUrlEventInput): object {
  const now = new Date();

  return {
    version: "2.0",
    routeKey: "$default",
    rawPath: input.path,
    rawQueryString: "",
    headers: input.headers,
    requestContext: {
      accountId: "anonymous",
      apiId: "async-invoke",
      domainName: "async-invoke",
      domainPrefix: "async-invoke",
      http: {
        method: input.method,
        path: input.path,
        protocol: "HTTP/1.1",
        sourceIp: "127.0.0.1",
        userAgent: "api-gateway-async-invoker",
      },
      requestId: `async-${now.getTime()}`,
      routeKey: "$default",
      stage: "$default",
      time: now.toUTCString(),
      timeEpoch: now.getTime(),
    },
    body: input.body.toString("base64"),
    isBase64Encoded: true,
  };
}
