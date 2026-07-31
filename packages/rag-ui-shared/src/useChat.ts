import axios, { AxiosInstance } from "axios";
import { useCallback, useState } from "react";

import { askQuestion } from "./rag.client";
import { ChatMessage } from "./types";

export interface UseChatResult {
  messages: ChatMessage[];
  isAsking: boolean;
  error: string | null;
  sendQuestion: (question: string) => Promise<void>;
  clearHistory: () => void;
}

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useChat(httpClient: AxiosInstance): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendQuestion = useCallback(
    async (question: string) => {
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

      setMessages((previous: ChatMessage[]) => [...previous, userMessage]);
      setIsAsking(true);
      setError(null);

      try {
        const result = await askQuestion(httpClient, trimmed);

        const assistantMessage: ChatMessage = {
          id: createId(),
          role: "assistant",
          content: result.answer,
          sources: result.sources,
          createdAt: new Date().toISOString(),
        };

        setMessages((previous: ChatMessage[]) => [
          ...previous,
          assistantMessage,
        ]);
      } catch (askError: unknown) {
        const message = axios.isAxiosError(askError)
          ? askError.response?.data?.error ??
            "The assistant is unavailable right now."
          : "The assistant is unavailable right now.";

        setError(message);
      } finally {
        setIsAsking(false);
      }
    },
    [httpClient]
  );

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, isAsking, error, sendQuestion, clearHistory };
}
