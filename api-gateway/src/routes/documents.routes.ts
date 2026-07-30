import { Router } from "express";

import {
  getDocumentStatus,
  ingestDocument,
} from "../controllers/documents.controller";
import { uploadPdf } from "../middleware/upload.middleware";

const router = Router();

router.post("/api/documents/ingest", uploadPdf, ingestDocument);
router.get("/api/documents/status/:documentId", getDocumentStatus);

export default router;
