"use client";

import { useEffect, useRef } from "react";
import { Trash2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import { useChat } from "../hooks/use-chat";
import type { Language } from "@/types";

interface ChatContainerProps {
  language?: Language;
}

const welcomeMessages: Record<Language, { title: string; subtitle: string; suggestions: string[] }> = {
  ko: {
    title: "안녕하세요! 저는 Spotfinder입니다",
    subtitle: "성수동 팝업스토어 탐험을 도와드릴게요. 무엇이 궁금하신가요?",
    suggestions: [
      "지금 진행 중인 팝업스토어 알려줘",
      "패션 관련 팝업 추천해줘",
      "오늘 성수동 일정 짜줘",
    ],
  },
  en: {
    title: "Hello! I'm Spotfinder",
    subtitle: "I'll help you explore Seongsu-dong popup stores. What would you like to know?",
    suggestions: [
      "Show me current popup stores",
      "Recommend fashion popups",
      "Plan my Seongsu itinerary",
    ],
  },
  ja: {
    title: "こんにちは！Spotfinderです",
    subtitle: "聖水洞のポップアップストア探索をお手伝いします。何かご質問はありますか？",
    suggestions: [
      "現在開催中のポップアップを教えて",
      "ファッション関連のポップアップを推薦して",
      "今日の聖水洞の予定を立てて",
    ],
  },
};

export function ChatContainer({ language = "ko" }: ChatContainerProps) {
  const { messages, isLoading, error, sendMessage, stopGeneration, clearMessages } = useChat(language);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const welcome = welcomeMessages[language];

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
            <Sparkles className="h-4 w-4 text-white" />
          </div>
          <div>
            <h2 className="font-semibold text-gray-900">AI 여행 가이드</h2>
            <p className="text-xs text-gray-500">Powered by Upstage Solar</p>
          </div>
        </div>

        {messages.length > 0 && (
          <Button variant="ghost" size="sm" onClick={clearMessages}>
            <Trash2 className="h-4 w-4 mr-1" />
            대화 지우기
          </Button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar bg-gray-50">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="h-16 w-16 rounded-full bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center mb-6">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              {welcome.title}
            </h3>
            <p className="text-gray-600 mb-8 max-w-sm">
              {welcome.subtitle}
            </p>

            {/* Suggestions */}
            <div className="flex flex-wrap justify-center gap-2">
              {welcome.suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => sendMessage(suggestion)}
                  className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-100 text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSend={sendMessage}
        onStop={stopGeneration}
        isLoading={isLoading}
        placeholder={
          language === "ko"
            ? "메시지를 입력하세요..."
            : language === "ja"
            ? "メッセージを入力..."
            : "Type a message..."
        }
      />
    </div>
  );
}
