import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import request from "supertest";
import type { Express } from "express";

const { mockGet, mockSend } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockSend: vi.fn(),
}));

vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({
      get: mockGet,
      post: vi.fn(),
    })),
  },
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

let app: Express;

describe("agent warmup", () => {
  beforeAll(async () => {
    process.env.RAG_CORE_FUNCTION_NAME = "rag-agent-rag-core";
    vi.resetModules();
    app = (await import("../app")).default;
  });

  beforeEach(() => {
    mockGet.mockReset();
    mockSend.mockReset();
  });

  it("starts RAG Core warmup asynchronously", async () => {
    mockSend.mockResolvedValue({ StatusCode: 202 });

    const response = await request(app).post("/api/warmup");

    expect(mockSend).toHaveBeenCalledTimes(1);
    expect(response.status).toBe(202);
    expect(response.body).toEqual({ status: "initializing" });
  });

  it("reports ready when RAG Core and Aurora respond", async () => {
    mockGet.mockResolvedValue({
      status: 200,
      data: { status: "ready" },
    });

    const response = await request(app).get("/api/warmup");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({ status: "ready" });
  });

  it("keeps initialization errors out of the chat error path", async () => {
    mockGet.mockRejectedValue(new Error("Function URL returned 502"));

    const response = await request(app).get("/api/warmup");

    expect(response.status).toBe(202);
    expect(response.body).toEqual({ status: "initializing" });
  });
});
