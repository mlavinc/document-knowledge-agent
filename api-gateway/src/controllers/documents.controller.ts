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

  if (documentsService.isAsyncMode()) {
    const accepted = await documentsService
      .ingestAsync(req.file)
      .catch((error) => {
        console.error("RAG Core invocation failed:", error?.message);
        throw new HttpError(503, "RAG Core unavailable");
      });

    res.status(202).json(accepted);
    return;
  }

  const result = await documentsService.ingest(req.file).catch((error) => {
    console.error("RAG Core call failed:", error?.message);
    throw new HttpError(503, "RAG Core unavailable");
  });

  res.json(result);
}

export async function getDocumentStatus(
  req: Request,
  res: Response
): Promise<void> {
  const rawId = req.params.documentId;
  const documentId = Array.isArray(rawId) ? rawId[0] : rawId;
  if (!documentId) {
    throw new HttpError(400, "documentId is required");
  }

  const status = await documentsService.getStatus(documentId).catch((error) => {
    console.error("RAG Core status call failed:", error?.message);
    throw new HttpError(503, "RAG Core unavailable");
  });

  res.json(status);
}
