"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { streamChatMessage, checkBackendHealth } from "@/lib/api";
import type { ChatMessage, Language } from "@/types";

function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
}

export function useChat(language: Language = "ko") {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendAvailable, setBackendAvailable] = useState<boolean | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Check backend availability on mount
  useEffect(() => {
    checkBackendHealth().then(setBackendAvailable);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setError(null);

      // Add user message
      const userMessage: ChatMessage = {
        id: generateId(),
        role: "user",
        content: content.trim(),
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      // Create placeholder for assistant message
      const assistantMessageId = generateId();
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      try {
        abortControllerRef.current = new AbortController();

        let accumulatedContent = "";
        let newThreadId = threadId;

        // Stream from Solar Pro 2 backend
        for await (const chunk of streamChatMessage(
          {
            message: content.trim(),
            thread_id: threadId || undefined,
            language,
          },
          abortControllerRef.current.signal
        )) {
          if (chunk.done) break;

          if (chunk.content) {
            accumulatedContent += chunk.content;
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: accumulatedContent }
                  : msg
              )
            );
          }

          if (chunk.thread_id && !newThreadId) {
            newThreadId = chunk.thread_id;
            setThreadId(chunk.thread_id);
          }
        }

        // If no content was received, show a fallback message
        if (!accumulatedContent) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content:
                      language === "ko"
                        ? "죄송합니다. 현재 AI 서비스에 연결할 수 없습니다. 잠시 후 다시 시도해주세요."
                        : language === "ja"
                        ? "申し訳ありません。現在AIサービスに接続できません。しばらくしてから再度お試しください。"
                        : "Sorry, unable to connect to the AI service. Please try again later.",
                  }
                : msg
            )
          );
        }
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          return;
        }

        console.error("Chat error:", err);

        // Show error in assistant message
        const errorMessage =
          language === "ko"
            ? "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요."
            : language === "ja"
            ? "バックエンドサーバーに接続できません。サーバーが起動しているか確認してください。"
            : "Cannot connect to backend server. Please make sure the server is running.";

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: errorMessage }
              : msg
          )
        );
        setError(errorMessage);
      } finally {
        setIsLoading(false);
        abortControllerRef.current = null;
      }
    },
    [isLoading, threadId, language]
  );

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setThreadId(null);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    threadId,
    backendAvailable,
    sendMessage,
    stopGeneration,
    clearMessages,
  };
}
