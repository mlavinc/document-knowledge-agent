import { Request, Response } from "express";

import { ragCoreClient } from "../clients/rag-core.client";
import { readCollectionHeader } from "../utils/collection";
import { HttpError } from "../utils/http-error";

export async function startWarmup(
  req: Request,
  res: Response
): Promise<void> {
  const collection = readCollectionHeader(
    req.headers as Record<string, unknown>
  );

  await ragCoreClient.startWarmup(collection).catch((error) => {
    console.error("RAG Core warmup invocation failed:", error?.message);
    throw new HttpError(503, "Could not initialize the agent");
  });

  res.status(202).json({ status: "initializing" });
}

export async function getWarmupStatus(
  req: Request,
  res: Response
): Promise<void> {
  const collection = readCollectionHeader(
    req.headers as Record<string, unknown>
  );

  try {
    const result = await ragCoreClient.getWarmupStatus(collection);
    res.status(result.statusCode).json(result.data);
  } catch (error) {
    // A cold RAG Core Function URL can briefly return 502 while its web
    // server starts. This is expected initialization, not a user-facing
    // chat failure.
    console.info(
      "RAG Core is still initializing:",
      error instanceof Error ? error.message : error
    );
    res.status(202).json({ status: "initializing" });
  }
}
