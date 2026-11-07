import multer, { FileFilterCallback } from "multer";
import { Request } from "express";

import { HttpError } from "../utils/http-error";

const storage = multer.memoryStorage();

function fileFilter(
  _req: Request,
  file: Express.Multer.File,
  callback: FileFilterCallback
): void {
  if (file.mimetype !== "application/pdf") {
    callback(new HttpError(400, "Only PDF files are allowed"));
    return;
  }

  callback(null, true);
}

export const uploadPdf = multer({
  storage,
  fileFilter,
  limits: { fileSize: 10 * 1024 * 1024 },
}).single("file");
