import { ChangeEvent, useRef, useState } from "react";

import { IngestedDocument } from "../types/rag.types";

interface DocumentUploadProps {
  documents: IngestedDocument[];
  isUploading: boolean;
  error: string | null;
  notice: string | null;
  onUpload: (file: File) => void;
}

export function DocumentUpload({
  documents,
  isUploading,
  error,
  notice,
  onUpload,
}: DocumentUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    const file = event.target.files?.[0];
    setSelectedFile(file ?? null);
  }

  function handleSubmit(): void {
    if (!selectedFile) {
      return;
    }

    onUpload(selectedFile);
    setSelectedFile(null);
    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  const lastDocument = documents[0];

  return (
    <section className="rounded-lg border border-sand-200 bg-white p-5 shadow-sm">
      <h2 className="font-serif text-lg text-ink">Document</h2>
      <p className="mt-1 text-sm text-ink/60">
        Upload a PDF to build a knowledge base you can question.
      </p>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="min-w-0 flex-1 cursor-pointer rounded-md border border-dashed border-sage-300 bg-sage-50 px-4 py-3 text-center text-sm text-sage-700 transition hover:bg-sage-100">
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleFileChange}
          />
          <span
            className="block truncate"
            title={selectedFile?.name}
          >
            {selectedFile ? selectedFile.name : "Choose a PDF file"}
          </span>
        </label>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={!selectedFile || isUploading}
          className="shrink-0 rounded-md bg-sage-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sage-700 disabled:cursor-not-allowed disabled:bg-sand-200 disabled:text-ink/40"
        >
          {isUploading ? "Processing…" : "Upload"}
        </button>
      </div>

      {error && (
        <p className="mt-3 rounded-md bg-clay-50 px-3 py-2 text-sm text-clay-500">
          {error}
        </p>
      )}

      {notice && !isUploading && (
        <p className="mt-3 rounded-md bg-sand-100 px-3 py-2 text-sm text-ink/70">
          {notice}
        </p>
      )}

      {lastDocument && !isUploading && lastDocument.status !== "processing" && (
        <p className="mt-3 min-w-0 rounded-md bg-sage-50 px-3 py-2 text-sm text-sage-700">
          <span
            className="block truncate font-medium"
            title={lastDocument.filename}
          >
            {lastDocument.filename}
          </span>{" "}
          processed into {lastDocument.chunks} chunks — status:{" "}
          {lastDocument.status}
        </p>
      )}

      {documents.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink/40">
            Processed documents
          </h3>
          <ul className="mt-2 space-y-1">
            {documents.map((document) => (
              <li
                key={`${document.filename}-${document.ingestedAt}`}
                className="flex min-w-0 items-center justify-between rounded-md bg-paper px-3 py-2 text-sm text-ink/70"
              >
                <span className="min-w-0 truncate" title={document.filename}>
                  {document.filename}
                </span>
                <span className="ml-2 shrink-0 text-xs text-ink/40">
                  {document.status === "processing"
                    ? "processing…"
                    : document.status === "failed"
                      ? "failed"
                      : `${document.chunks ?? 0} chunks`}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
