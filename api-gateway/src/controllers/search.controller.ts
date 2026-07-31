import { Request, Response } from "express";

import { ragService } from "../services/rag.service";
import { readCollectionHeader } from "../utils/collection";
import { HttpError } from "../utils/http-error";
import { SearchRequestBody } from "../types/search.types";

export async function search(
  req: Request<unknown, unknown, SearchRequestBody>,
  res: Response
): Promise<void> {
  const { question } = req.body;
  const collection = readCollectionHeader(
    req.headers as Record<string, unknown>
  );

  const result = await ragService.search(question, collection).catch((error) => {
    console.error("RAG Core call failed:", error?.message);
    throw new HttpError(503, "RAG Core unavailable");
  });

  res.json(result);
}
