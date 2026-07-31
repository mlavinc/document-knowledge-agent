import { ChatMessage } from "@rag-agent/ui-shared";

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
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
