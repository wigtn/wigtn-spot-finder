"use client";

import { PopupCard } from "./popup-card";
import { CardSkeleton } from "@/components/ui";
import type { PopupSummary } from "@/types";
import { Package } from "lucide-react";

interface PopupGridProps {
  popups: PopupSummary[];
  loading?: boolean;
}

export function PopupGrid({ popups, loading }: PopupGridProps) {
  if (loading) {
    return (
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (popups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <Package className="h-16 w-16 text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          팝업스토어가 없습니다
        </h3>
        <p className="text-gray-500">
          다른 카테고리를 선택하거나 검색어를 변경해보세요.
        </p>
      </div>
    );
  }

  return (
    <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {popups.map((popup) => (
        <PopupCard key={popup.id} popup={popup} />
      ))}
    </div>
  );
}
