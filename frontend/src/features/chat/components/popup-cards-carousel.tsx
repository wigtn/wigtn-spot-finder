"use client";

import { PopupCardMini } from "./popup-card-mini";
import type { ChatPopupCard } from "@/types";

interface PopupCardsCarouselProps {
  popups: ChatPopupCard[];
}

export function PopupCardsCarousel({ popups }: PopupCardsCarouselProps) {
  if (!popups || popups.length === 0) {
    return null;
  }

  return (
    <div className="mt-3 -mx-1">
      <div
        className="flex gap-2 overflow-x-auto pb-2 px-1 snap-x snap-mandatory scrollbar-thin"
      >
        {popups.map((popup) => (
          <PopupCardMini key={popup.id} popup={popup} />
        ))}
      </div>
    </div>
  );
}
