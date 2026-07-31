import { FormEvent, useEffect, useRef, useState } from "react";

import { ChatMessage } from "../types/chat.types";
import { MessageBubble } from "./MessageBubble";

const SUGGESTIONS = [
  "Who are you?",
  "Tell me about your experience.",
  "What projects have you built?",
  "What AWS technologies have you used?",
  "What did you build at Nestlé?",
  "Explain your Document Knowledge Agent.",
];

interface ChatPanelProps {
  messages: ChatMessage[];
  isAsking: boolean;
  error: string | null;
  onAsk: (question: string) => void;
}

export function ChatPanel({
  messages,
  isAsking,
  error,
  onAsk,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const scrollAnchorRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollAnchorRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAsking]);

  function handleSubmit(event: FormEvent): void {
    event.preventDefault();
    if (!input.trim() || isAsking) {
      return;
    }
    onAsk(input);
    setInput("");
  }

  return (
    <section className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto px-1 py-2 sm:px-0">
        {messages.length === 0 && (
          <ul className="flex flex-col gap-2 animate-fade-up-delay-2">
            {SUGGESTIONS.map((suggestion) => (
              <li key={suggestion}>
                <button
                  type="button"
                  onClick={() => onAsk(suggestion)}
                  className="w-full rounded-xl border border-ash-800 bg-transparent px-4 py-3 text-left text-sm text-ash-200 transition hover:border-ash-600 hover:bg-ash-900 hover:text-snow"
                >
                  <span className="mr-2 text-ash-500">•</span>
                  {suggestion}
                </button>
              </li>
            ))}
          </ul>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isAsking && (
          <div className="flex justify-start animate-fade-up">
            <div className="flex items-center gap-1.5 rounded-2xl rounded-bl-md border border-ash-800 bg-ash-900/80 px-4 py-3">
              <span className="h-1.5 w-1.5 rounded-full bg-ash-400 animate-blink" />
              <span
                className="h-1.5 w-1.5 rounded-full bg-ash-400 animate-blink"
                style={{ animationDelay: "0.2s" }}
              />
              <span
                className="h-1.5 w-1.5 rounded-full bg-ash-400 animate-blink"
                style={{ animationDelay: "0.4s" }}
              />
            </div>
          </div>
        )}

        <div ref={scrollAnchorRef} />
      </div>

      {error && (
        <p className="mb-3 rounded-xl border border-ash-700 bg-ash-900 px-3 py-2 text-sm text-ash-200">
          {error}
        </p>
      )}

      <form
        onSubmit={handleSubmit}
        className="mt-2 flex flex-col gap-3 border-t border-ash-800 pt-4 sm:flex-row sm:items-center"
      >
        <label className="sr-only" htmlFor="portfolio-question">
          Your question
        </label>
        <input
          id="portfolio-question"
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Type your question..."
          autoComplete="off"
          className="min-w-0 flex-1 rounded-xl border border-ash-800 bg-ink px-4 py-3 text-sm text-snow outline-none placeholder:text-ash-500 focus:border-ash-500"
        />
        <button
          type="submit"
          disabled={isAsking || !input.trim()}
          className="shrink-0 rounded-xl bg-snow px-5 py-3 text-sm font-semibold text-ink transition hover:bg-ash-100 disabled:cursor-not-allowed disabled:bg-ash-800 disabled:text-ash-500"
        >
          Send
        </button>
      </form>
    </section>
  );
}
