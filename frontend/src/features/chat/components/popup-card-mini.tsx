"use client";

import Link from "next/link";
import { MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import { CategoryBadge } from "@/components/ui/badge";
import type { ChatPopupCard } from "@/types";

interface PopupCardMiniProps {
  popup: ChatPopupCard;
  className?: string;
}

function formatEndDate(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  return `~${month}.${day}`;
}

export function PopupCardMini({ popup, className }: PopupCardMiniProps) {
  return (
    <Link href={`/popups/${popup.id}`}>
      <div
        className={cn(
          "flex-shrink-0 w-36 bg-white rounded-xl border border-gray-200 overflow-hidden",
          "hover:border-primary-300 hover:shadow-md transition-all duration-200",
          "snap-start",
          className
        )}
      >
        {/* Thumbnail */}
        <div className="relative h-20 bg-gray-100">
          {popup.thumbnail_url ? (
            <img
              src={popup.thumbnail_url}
              alt={popup.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-300">
              <MapPin className="h-8 w-8" />
            </div>
          )}

          {/* Category Badge - Small */}
          <div className="absolute top-1.5 left-1.5">
            <CategoryBadge category={popup.category} className="text-[10px] px-1.5 py-0.5" />
          </div>

          {/* Active Status */}
          {popup.is_active && (
            <div className="absolute top-1.5 right-1.5">
              <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-green-500 text-white text-[10px] font-medium">
                <span className="w-1 h-1 rounded-full bg-white animate-pulse" />
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-2 space-y-1">
          {/* Title - 2 lines max */}
          <h4 className="text-xs font-medium text-gray-900 line-clamp-2 leading-tight">
            {popup.name_korean || popup.name}
          </h4>

          {/* End Date */}
          {popup.period_end && (
            <p className="text-[10px] text-gray-500">
              {formatEndDate(popup.period_end)}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}
