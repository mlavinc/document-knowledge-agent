import { beforeEach, describe, expect, it, vi } from "vitest";
import request from "supertest";

const { mockPost } = vi.hoisted(() => ({
  mockPost: vi.fn(),
}));

vi.mock("axios", () => ({
  default: {
    create: vi.fn(() => ({ post: mockPost })),
  },
}));

import app from "../app";

describe("POST /api/search proxy", () => {
  beforeEach(() => {
    mockPost.mockReset();
  });

  it("forwards the request internally to RAG Core's POST /api/v1/search", async () => {
    mockPost.mockResolvedValue({
      data: { answer: "mock answer", sources: [] },
    });

    const response = await request(app)
      .post("/api/search")
      .send({ question: "What is PyramidTNT?" });

    expect(mockPost).toHaveBeenCalledWith(
      "/api/v1/search",
      JSON.stringify({ question: "What is PyramidTNT?" }),
      {
        headers: {
          "Content-Type": "application/json",
          "x-rag-collection": "default",
        },
      }
    );
    expect(response.status).toBe(200);
    expect(response.body).toEqual({ answer: "mock answer", sources: [] });
  });

  it("returns 503 when RAG Core is unreachable", async () => {
    mockPost.mockRejectedValue(new Error("connection refused"));

    const response = await request(app)
      .post("/api/search")
      .send({ question: "What is PyramidTNT?" });

    expect(response.status).toBe(503);
    expect(response.body).toEqual({ error: "RAG Core unavailable" });
  });
});
