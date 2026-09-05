import axios from "axios";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  askQuestion,
  getAgentWarmupStatus,
  startAgentWarmup,
} from "../api/rag.client";
import { AgentStatus, ChatMessage } from "../types/rag.types";

interface UseChatResult {
  messages: ChatMessage[];
  isAsking: boolean;
  agentStatus: AgentStatus;
  error: string | null;
  sendQuestion: (question: string) => Promise<void>;
  clearHistory: () => void;
}

const WARMUP_POLL_INTERVAL_MS = 5000;
const WARMUP_INITIAL_POLL_DELAY_MS = 20_000;
const WARMUP_TIMEOUT_MS = 90_000;

function createId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [agentStatus, setAgentStatus] =
    useState<AgentStatus>("initializing");
  const [error, setError] = useState<string | null>(null);
  const pendingQuestion = useRef<string | null>(null);

  const runQuestion = useCallback(async (question: string) => {
    try {
      const result = await askQuestion(question);

      const assistantMessage: ChatMessage = {
        id: createId(),
        role: "assistant",
        content: result.answer,
        sources: result.sources,
        createdAt: new Date().toISOString(),
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch (askError) {
      const message = axios.isAxiosError(askError)
        ? askError.response?.data?.error ?? "The assistant is unavailable right now."
        : "The assistant is unavailable right now.";

      setError(message);
    } finally {
      setIsAsking(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    let pollTimer: number | undefined;
    const startedAt = Date.now();

    const pollStatus = async () => {
      if (cancelled) {
        return;
      }

      try {
        const result = await getAgentWarmupStatus();
        if (result.status === "ready") {
          setAgentStatus("ready");
          return;
        }
      } catch {
        // RAG Core can return a transient 502 while its container starts.
      }

      if (Date.now() - startedAt >= WARMUP_TIMEOUT_MS) {
        setAgentStatus("unavailable");
        pendingQuestion.current = null;
        setIsAsking(false);
        setError("The agent could not finish initializing. Please retry.");
        return;
      }

      pollTimer = window.setTimeout(
        pollStatus,
        WARMUP_POLL_INTERVAL_MS
      );
    };

    const initialize = async () => {
      try {
        await startAgentWarmup();
      } catch {
        // Status polling distinguishes a transient cold start from failure.
      }
      pollTimer = window.setTimeout(
        pollStatus,
        WARMUP_INITIAL_POLL_DELAY_MS
      );
    };

    void initialize();

    return () => {
      cancelled = true;
      if (pollTimer !== undefined) {
        window.clearTimeout(pollTimer);
      }
    };
  }, []);

  useEffect(() => {
    if (agentStatus !== "ready" || !pendingQuestion.current) {
      return;
    }

    const question = pendingQuestion.current;
    pendingQuestion.current = null;
    void runQuestion(question);
  }, [agentStatus, runQuestion]);

  const sendQuestion = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || isAsking) {
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

      if (agentStatus !== "initializing") {
        await runQuestion(trimmed);
        return;
      }

      pendingQuestion.current = trimmed;
    },
    [agentStatus, isAsking, runQuestion]
  );

  const clearHistory = useCallback(() => {
    pendingQuestion.current = null;
    setMessages([]);
    setIsAsking(false);
    setError(null);
  }, []);

  return {
    messages,
    isAsking,
    agentStatus,
    error,
    sendQuestion,
    clearHistory,
  };
}
