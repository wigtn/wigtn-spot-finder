"use client";

import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/types";
import { parseMessageContent } from "../utils/parse-message-content";
import { PopupCardsCarousel } from "./popup-cards-carousel";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  // Parse message content to extract popup cards
  const parsedContent = useMemo(() => {
    if (!message.content || isUser) {
      return { textBefore: message.content || "", textAfter: "", popupCards: null };
    }
    return parseMessageContent(message.content);
  }, [message.content, isUser]);

  const hasPopupCards = parsedContent.popupCards && parsedContent.popupCards.length > 0;
  const displayText = parsedContent.textBefore + (parsedContent.textAfter ? "\n\n" + parsedContent.textAfter : "");

  return (
    <div
      className={cn(
        "flex gap-3 animate-fade-in",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center",
          isUser ? "bg-primary-600" : "bg-gradient-to-br from-primary-500 to-accent-500"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-white" />
        ) : (
          <Bot className="h-4 w-4 text-white" />
        )}
      </div>

      {/* Message Bubble */}
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-3",
          isUser
            ? "bg-primary-600 text-white rounded-tr-sm"
            : "bg-white border border-gray-200 text-gray-900 rounded-tl-sm",
          hasPopupCards && "max-w-[90%]"
        )}
      >
        {/* Text Content */}
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {displayText || (
            <span className="inline-flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </span>
          )}
        </div>

        {/* Popup Cards Carousel */}
        {hasPopupCards && (
          <PopupCardsCarousel popups={parsedContent.popupCards!} />
        )}
      </div>
    </div>
  );
}
