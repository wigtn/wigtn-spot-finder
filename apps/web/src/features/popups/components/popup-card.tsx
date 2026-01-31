"use client";

import Image from "next/image";
import Link from "next/link";
import { Calendar, MapPin, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui";
import { CategoryBadge } from "@/components/ui/badge";
import { formatDateRange } from "@/lib/utils";
import type { PopupSummary } from "@/types";

interface PopupCardProps {
  popup: PopupSummary;
}

export function PopupCard({ popup }: PopupCardProps) {
  return (
    <Link href={`/popups/${popup.id}`}>
      <Card hover className="h-full group">
        {/* Thumbnail */}
        <div className="relative h-48 bg-gray-100">
          {popup.thumbnail_url ? (
            <img
              src={popup.thumbnail_url}
              alt={popup.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <MapPin className="h-12 w-12" />
            </div>
          )}

          {/* Category Badge */}
          <div className="absolute top-3 left-3">
            <CategoryBadge category={popup.category} />
          </div>

          {/* Active Status */}
          {popup.is_active && (
            <div className="absolute top-3 right-3">
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-green-500 text-white text-xs font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                진행중
              </span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4 space-y-3">
          {/* Title */}
          <div>
            <h3 className="font-semibold text-gray-900 line-clamp-1 group-hover:text-primary-600 transition-colors">
              {popup.name_korean || popup.name}
            </h3>
            {popup.name_korean && popup.name !== popup.name_korean && (
              <p className="text-sm text-gray-500 line-clamp-1">{popup.name}</p>
            )}
          </div>

          {/* Location */}
          <div className="flex items-center gap-1.5 text-sm text-gray-600">
            <MapPin className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">{popup.location}</span>
          </div>

          {/* Period */}
          <div className="flex items-center gap-1.5 text-sm text-gray-600">
            <Calendar className="h-4 w-4 flex-shrink-0" />
            <span>{formatDateRange(popup.period_start, popup.period_end)}</span>
          </div>
        </div>
      </Card>
    </Link>
  );
}
