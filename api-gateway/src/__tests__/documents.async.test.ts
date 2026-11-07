import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import request from "supertest";
import type { Express } from "express";

const { mockRemove, mockSend, mockStage } = vi.hoisted(() => ({
  mockRemove: vi.fn(),
  mockSend: vi.fn(),
  mockStage: vi.fn(),
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

vi.mock("../services/staged-documents.service", () => ({
  stagedDocumentsService: {
    stage: mockStage,
    remove: mockRemove,
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
    mockStage.mockReset();
    mockRemove.mockReset();
    mockStage.mockResolvedValue({
      documentId: "paper.pdf",
      objectKey: "staging/default/upload-paper.pdf",
    });
    mockRemove.mockResolvedValue(undefined);
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
    const invocation = mockSend.mock.calls[0]?.[0] as {
      input: { Payload: Uint8Array };
    };
    const event = JSON.parse(Buffer.from(invocation.input.Payload).toString());
    const stagedBody = JSON.parse(
      Buffer.from(event.body, "base64").toString("utf8")
    );
    expect(event.rawPath).toBe("/api/v1/documents/ingest-staged");
    expect(stagedBody).toEqual({
      document_id: "paper.pdf",
      object_key: "staging/default/upload-paper.pdf",
    });
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
    expect(mockRemove).toHaveBeenCalledWith(
      "staging/default/upload-paper.pdf"
    );
  });
});
