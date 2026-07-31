import ReactMarkdown from "react-markdown";

import { ChatMessage } from "../types/chat.types";

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex animate-fade-up ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[min(100%,34rem)] px-4 py-3 text-[0.95rem] leading-relaxed ${
          isUser
            ? "rounded-2xl rounded-br-md bg-snow text-ink"
            : "rounded-2xl rounded-bl-md border border-ash-800 bg-ash-900/80 text-chalk"
        }`}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="assistant-md">
            <ReactMarkdown
              components={{
                p: ({ children }) => (
                  <p className="mb-2 last:mb-0 whitespace-pre-wrap">{children}</p>
                ),
                strong: ({ children }) => (
                  <strong className="font-semibold text-snow">{children}</strong>
                ),
                em: ({ children }) => <em className="italic text-ash-100">{children}</em>,
                ul: ({ children }) => (
                  <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">
                    {children}
                  </ol>
                ),
                li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="underline decoration-ash-600 underline-offset-2 transition hover:text-snow hover:decoration-ash-300"
                  >
                    {children}
                  </a>
                ),
                code: ({ children }) => (
                  <code className="rounded bg-ink/60 px-1 py-0.5 text-[0.85em] text-ash-100">
                    {children}
                  </code>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
