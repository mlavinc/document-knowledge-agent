import { ChatPanel } from "./components/ChatPanel";
import { usePortfolioChat } from "./hooks/usePortfolioChat";

function App() {
  const { messages, isAsking, error, sendQuestion } = usePortfolioChat();

  return (
    <div className="mx-auto flex min-h-full w-full max-w-xl flex-col px-4 pb-8 pt-12 sm:px-6 sm:pb-12 sm:pt-16">
      <header className="mb-8 border-b border-ash-800 pb-8 text-left sm:mb-10 sm:pb-10">
        <h1 className="animate-fade-up font-display text-3xl font-bold tracking-tight text-snow sm:text-4xl">
          Ask me anything
        </h1>
        <p className="mt-4 max-w-md animate-fade-up-delay text-sm leading-relaxed text-ash-400 sm:text-base">
          You can ask about my experience, projects, AWS, backend development,
          cloud engineering or education.
        </p>
      </header>

      <main className="flex min-h-[min(62vh,32rem)] flex-1 flex-col animate-fade-up-delay-2">
        <ChatPanel
          messages={messages}
          isAsking={isAsking}
          error={error}
          onAsk={sendQuestion}
        />
      </main>
    </div>
  );
}

export default App;
