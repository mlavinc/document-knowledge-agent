import { Request, Response } from "express";

import { documentsService } from "../services/documents.service";
import { HttpError } from "../utils/http-error";

export async function ingestDocument(
  req: Request,
  res: Response
): Promise<void> {
  if (!req.file) {
    throw new HttpError(400, "file is required");
  }

  const result = await documentsService.ingest(req.file).catch((error) => {
    console.error("RAG Core call failed:", error?.message);
    throw new HttpError(503, "RAG Core unavailable");
  });

  res.json(result);
}
