import axios from "axios";
import { useCallback, useState } from "react";

import { askQuestion } from "../api/search.client";
import { ChatMessage } from "../types/chat.types";

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

/** Portfolio chat — search only; never touches document ingest APIs. */
export function usePortfolioChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendQuestion = useCallback(async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };

    setMessages((previous) => [...previous, userMessage]);
    setIsAsking(true);
    setError(null);

    try {
      const result = await askQuestion(trimmed);

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: result.answer,
        sources: result.sources,
        createdAt: new Date().toISOString(),
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch (askError: unknown) {
      const message = axios.isAxiosError(askError)
        ? askError.response?.data?.error ??
          "The assistant is unavailable right now."
        : "The assistant is unavailable right now.";

      setError(message);
    } finally {
      setIsAsking(false);
    }
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isAsking, error, sendQuestion, clearHistory };
}
