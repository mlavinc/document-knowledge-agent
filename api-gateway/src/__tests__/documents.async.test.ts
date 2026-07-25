import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import request from "supertest";
import type { Express } from "express";

const { mockSend } = vi.hoisted(() => ({
  mockSend: vi.fn(),
}));

vi.mock("@aws-sdk/client-lambda", () => ({
  LambdaClient: class {
    send = mockSend;
  },
  InvokeCommand: class {
    input: unknown;
    constructor(input: unknown) {
      this.input = input;
    }
  },
}));

// env.ts reads process.env at module-load time, so INGESTION_MODE must be
// set and modules re-imported fresh (isolated from other test files'
// cached "sync" default) before pulling in the app.
let app: Express;

describe("POST /api/documents/ingest (INGESTION_MODE=async)", () => {
  beforeAll(async () => {
    process.env.INGESTION_MODE = "async";
    process.env.RAG_CORE_FUNCTION_NAME = "rag-agent-rag-core";
    vi.resetModules();
    app = (await import("../app")).default;
  });

  beforeEach(() => {
    mockSend.mockReset();
  });

  it("invokes rag-core asynchronously and responds 202 immediately", async () => {
    mockSend.mockResolvedValue({ StatusCode: 202 });

    const response = await request(app)
      .post("/api/documents/ingest")
      .attach("file", Buffer.from("%PDF-1.4 mock content"), {
        filename: "paper.pdf",
        contentType: "application/pdf",
      });

    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(response.status).toBe(202);
    expect(response.body).toEqual({
      document_id: "paper.pdf",
      filename: "paper.pdf",
      status: "processing",
    });
  });

  it("returns 503 when the async invocation itself fails", async () => {
    mockSend.mockRejectedValue(new Error("AccessDenied"));

    const response = await request(app)
      .post("/api/documents/ingest")
      .attach("file", Buffer.from("%PDF-1.4 mock content"), {
        filename: "paper.pdf",
        contentType: "application/pdf",
      });

    expect(response.status).toBe(503);
    expect(response.body).toEqual({ error: "RAG Core unavailable" });
  });
});
