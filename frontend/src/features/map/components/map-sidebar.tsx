"use client";

import { X, MapPin, Calendar, Clock, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui";
import { CategoryBadge } from "@/components/ui/badge";
import { formatDateRange } from "@/lib/utils";
import type { PopupStore } from "@/types";

interface MapSidebarProps {
  popup: PopupStore | null;
  onClose: () => void;
}

export function MapSidebar({ popup, onClose }: MapSidebarProps) {
  if (!popup) return null;

  const naverMapUrl = `https://map.naver.com/v5/search/${encodeURIComponent(popup.address)}`;

  return (
    <div className="absolute top-4 right-4 w-80 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-10 animate-slide-up">
      {/* Header */}
      <div className="relative h-40 bg-gray-100">
        {popup.thumbnail_url ? (
          <img
            src={popup.thumbnail_url}
            alt={popup.name}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <MapPin className="h-12 w-12 text-gray-300" />
          </div>
        )}

        <button
          onClick={onClose}
          className="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full hover:bg-white transition-colors"
        >
          <X className="h-4 w-4 text-gray-600" />
        </button>

        <div className="absolute bottom-2 left-2">
          <CategoryBadge category={popup.category} />
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        <div>
          <h3 className="font-semibold text-gray-900">{popup.name_korean}</h3>
          {popup.name !== popup.name_korean && (
            <p className="text-sm text-gray-500">{popup.name}</p>
          )}
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex items-start gap-2 text-gray-600">
            <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span>{popup.address}</span>
          </div>

          <div className="flex items-center gap-2 text-gray-600">
            <Calendar className="h-4 w-4 flex-shrink-0" />
            <span>{formatDateRange(popup.period_start, popup.period_end)}</span>
          </div>

          <div className="flex items-center gap-2 text-gray-600">
            <Clock className="h-4 w-4 flex-shrink-0" />
            <span>{popup.operating_hours}</span>
          </div>
        </div>

        <Button
          size="sm"
          className="w-full"
          onClick={() => window.open(naverMapUrl, "_blank")}
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          네이버 지도로 보기
        </Button>
      </div>
    </div>
  );
}
