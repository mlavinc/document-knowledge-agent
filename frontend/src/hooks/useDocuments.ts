import axios from "axios";
import { useCallback, useRef, useState } from "react";

import { getDocumentStatus, ingestDocument } from "../api/documents.client";
import { IngestedDocument } from "../types/rag.types";

interface UseDocumentsResult {
  documents: IngestedDocument[];
  isUploading: boolean;
  error: string | null;
  notice: string | null;
  uploadDocument: (file: File) => Promise<void>;
}

const POLL_INTERVAL_MS = 3000;
const POLL_TIMEOUT_MS = 5 * 60 * 1000;

export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<IngestedDocument[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const pollTimers = useRef<Map<string, number>>(new Map());

  const stopPolling = useCallback((documentId: string) => {
    const timer = pollTimers.current.get(documentId);
    if (timer !== undefined) {
      window.clearInterval(timer);
      pollTimers.current.delete(documentId);
    }
  }, []);

  const startPolling = useCallback(
    (documentId: string) => {
      stopPolling(documentId);
      const startedAt = Date.now();

      const timer = window.setInterval(async () => {
        if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
          stopPolling(documentId);
          setDocuments((previous) =>
            previous.map((doc) =>
              doc.filename === documentId
                ? { ...doc, status: "failed" }
                : doc
            )
          );
          setError(
            `"${documentId}" is still processing after several minutes. Check logs or retry.`
          );
          setNotice(null);
          return;
        }

        try {
          const status = await getDocumentStatus(documentId);
          if (status.status === "processing") {
            return;
          }

          stopPolling(documentId);
          setDocuments((previous) =>
            previous.map((doc) =>
              doc.filename === documentId
                ? {
                    ...doc,
                    status: status.status,
                    chunks: status.chunks,
                  }
                : doc
            )
          );

          if (status.status === "completed") {
            setNotice(
              `"${documentId}" is ready (${status.chunks ?? 0} chunks).`
            );
            setError(null);
          } else if (status.status === "failed") {
            setError(
              status.error ??
                `"${documentId}" failed during background processing.`
            );
            setNotice(null);
          }
        } catch {
          // Transient errors while polling: keep trying until timeout.
        }
      }, POLL_INTERVAL_MS);

      pollTimers.current.set(documentId, timer);
    },
    [stopPolling]
  );

  const uploadDocument = useCallback(
    async (file: File) => {
      setIsUploading(true);
      setError(null);
      setNotice(null);

      try {
        const result = await ingestDocument(file);
        const documentId = result.document_id ?? result.filename;

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
            `"${result.filename}" is being processed in the background…`
          );
          startPolling(documentId);
        }
      } catch (uploadError) {
        const message = axios.isAxiosError(uploadError)
          ? uploadError.response?.data?.error ??
            "Could not process the document."
          : "Could not process the document.";

        setError(message);
      } finally {
        setIsUploading(false);
      }
    },
    [startPolling]
  );

  return { documents, isUploading, error, notice, uploadDocument };
}
