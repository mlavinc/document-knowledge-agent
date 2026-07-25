import axios from "axios";
import { useCallback, useState } from "react";

import { ingestDocument } from "../api/documents.client";
import { IngestedDocument } from "../types/rag.types";

interface UseDocumentsResult {
  documents: IngestedDocument[];
  isUploading: boolean;
  error: string | null;
  notice: string | null;
  uploadDocument: (file: File) => Promise<void>;
}

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<IngestedDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const uploadDocument = useCallback(async (file: File) => {
    setIsUploading(true);
    setError(null);
    setNotice(null);

    try {
      const result = await ingestDocument(file);

      setDocuments((previous) => [
        {
          filename: result.filename,
          chunks: result.chunks,
          status: result.status,
          ingestedAt: new Date().toISOString(),
        },
        ...previous,
      ]);

      if (result.status === "processing") {
        setNotice(
          `"${result.filename}" is being processed in the background. This can take a few minutes for large documents — you can start asking questions once it finishes.`
        );
      }
    } catch (uploadError) {
      const message = axios.isAxiosError(uploadError)
        ? uploadError.response?.data?.error ?? "Could not process the document."
        : "Could not process the document.";

      setError(message);
    } finally {
      setIsUploading(false);
    }
  }, []);

  return { documents, isUploading, error, notice, uploadDocument };
}
