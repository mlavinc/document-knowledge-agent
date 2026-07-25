import { ChatWindow } from "./components/ChatWindow";
import { DocumentUpload } from "./components/DocumentUpload";
import { ExportButton } from "./components/ExportButton";
import { HistoryPanel } from "./components/HistoryPanel";
import { useChat } from "./hooks/useChat";
import { useDocuments } from "./hooks/useDocuments";

function App() {
  const {
    documents,
    isUploading,
    error: uploadError,
    notice: uploadNotice,
    uploadDocument,
  } = useDocuments();
  const {
    messages,
    isAsking,
    error: chatError,
    sendQuestion,
    clearHistory,
  } = useChat();

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-sand-200 bg-white/60">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <h1 className="font-serif text-2xl text-ink">
              RAG Document Knowledge
            </h1>
            <p className="text-sm text-ink/50">
              Upload a paper, ask questions, review the sources.
            </p>
          </div>
          <ExportButton messages={messages} />
        </div>
      </header>

      <main className="mx-auto grid max-w-6xl grid-cols-1 gap-5 px-6 py-6 lg:grid-cols-[320px_1fr]">
        <aside className="flex flex-col gap-5">
          <DocumentUpload
            documents={documents}
            isUploading={isUploading}
            error={uploadError}
            notice={uploadNotice}
            onUpload={uploadDocument}
          />
          <HistoryPanel messages={messages} onClear={clearHistory} />
        </aside>

        <div className="h-[70vh] min-h-[480px]">
          <ChatWindow
            messages={messages}
            isAsking={isAsking}
            error={chatError}
            onAsk={sendQuestion}
          />
        </div>
      </main>
    </div>
  );
}

export default App;
