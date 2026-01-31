"use client";

import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { Send, StopCircle } from "lucide-react";
import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  onSend,
  onStop,
  isLoading,
  disabled,
  placeholder = "메시지를 입력하세요...",
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  }, [message]);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !disabled) {
      onSend(message);
      setMessage("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-end gap-2 p-4 bg-white border-t border-gray-200">
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className={cn(
              "w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12",
              "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
              "placeholder:text-gray-400 text-gray-900",
              "disabled:bg-gray-100 disabled:cursor-not-allowed",
              "max-h-[150px]"
            )}
          />
        </div>

        {isLoading ? (
          <Button
            type="button"
            variant="danger"
            size="lg"
            onClick={onStop}
            className="flex-shrink-0"
          >
            <StopCircle className="h-5 w-5" />
          </Button>
        ) : (
          <Button
            type="submit"
            size="lg"
            disabled={!message.trim() || disabled}
            className="flex-shrink-0"
          >
            <Send className="h-5 w-5" />
          </Button>
        )}
      </div>
    </form>
  );
}
