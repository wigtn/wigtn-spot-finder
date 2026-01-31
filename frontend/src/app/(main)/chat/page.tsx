"use client";

import { ChatContainer } from "@/features/chat/components";
import { useLanguage } from "@/contexts/language-context";
import type { Language } from "@/types";

const pageContent: Record<Language, { title: string; subtitle: string }> = {
  ja: {
    title: "AI旅行ガイド",
    subtitle: "聖水洞のポップアップストアについて何でも聞いてください",
  },
  en: {
    title: "AI Travel Guide",
    subtitle: "Ask me anything about popup stores in Seongsu-dong",
  },
  ko: {
    title: "AI 여행 가이드",
    subtitle: "성수동 팝업스토어에 대해 무엇이든 물어보세요",
  },
};

export default function ChatPage() {
  const { language } = useLanguage();
  const t = pageContent[language];

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Header */}
      <div className="px-4 py-3 bg-white border-b border-gray-100">
        <h1 className="text-lg font-semibold text-gray-900">{t.title}</h1>
        <p className="text-sm text-gray-500">{t.subtitle}</p>
      </div>

      {/* Chat */}
      <div className="flex-1 overflow-hidden">
        <ChatContainer language={language} />
      </div>
    </div>
  );
}
