import { Request, Response } from "express";

import { ragService } from "../services/rag.service";
import { HttpError } from "../utils/http-error";
import { SearchRequestBody } from "../types/search.types";

export async function search(
  req: Request<unknown, unknown, SearchRequestBody>,
  res: Response
): Promise<void> {
  const { question } = req.body;

  const result = await ragService.search(question).catch((error) => {
    console.error("RAG Core call failed:", error?.message);
    throw new HttpError(503, "RAG Core unavailable");
  });

  res.json(result);
}
