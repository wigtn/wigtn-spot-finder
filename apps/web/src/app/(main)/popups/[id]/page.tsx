"use client";

import { useState, useEffect } from "react";
import { notFound, useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Calendar,
  Clock,
  MapPin,
  ExternalLink,
  Instagram,
  Navigation,
} from "lucide-react";
import { getPopupById } from "@/lib/popup-data";
import { CategoryBadge } from "@/components/ui/badge";
import { formatDateRange } from "@/lib/utils";
import { useLanguage } from "@/contexts/language-context";
import type { PopupStore, Language } from "@/types";

const pageLabels: Record<Language, {
  back: string;
  ongoing: string;
  ended: string;
  period: string;
  hours: string;
  location: string;
  about: string;
  naverMap: string;
  googleMaps: string;
}> = {
  ja: {
    back: "一覧に戻る",
    ongoing: "開催中",
    ended: "終了",
    period: "開催期間",
    hours: "営業時間",
    location: "場所",
    about: "紹介",
    naverMap: "Naverマップ",
    googleMaps: "Google Maps",
  },
  en: {
    back: "Back to list",
    ongoing: "Ongoing",
    ended: "Ended",
    period: "Period",
    hours: "Hours",
    location: "Location",
    about: "About",
    naverMap: "Naver Map",
    googleMaps: "Google Maps",
  },
  ko: {
    back: "목록으로",
    ongoing: "진행중",
    ended: "종료됨",
    period: "운영 기간",
    hours: "영업 시간",
    location: "위치",
    about: "소개",
    naverMap: "네이버 지도",
    googleMaps: "Google Maps",
  },
};

export default function PopupDetailPage() {
  const params = useParams();
  const { language } = useLanguage();
  const t = pageLabels[language];
  const [popup, setPopup] = useState<PopupStore | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = params.id as string;
    const data = getPopupById(id);
    setPopup(data);
    setLoading(false);
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!popup) {
    notFound();
  }

  const naverMapUrl = `https://map.naver.com/v5/search/${encodeURIComponent(popup.address)}`;
  const googleMapUrl = popup.coordinates
    ? `https://www.google.com/maps?q=${popup.coordinates.latitude},${popup.coordinates.longitude}`
    : `https://www.google.com/maps/search/${encodeURIComponent(popup.address)}`;

  // Get localized description
  const getDescription = () => {
    if (language === "ja" && popup.description_ja) return popup.description_ja;
    if (language === "en" && popup.description_en) return popup.description_en;
    return popup.description;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back Button */}
      <div className="bg-white border-b border-gray-200">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-4">
          <Link
            href="/popups"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            {t.back}
          </Link>
        </div>
      </div>

      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-2xl border border-gray-200 overflow-hidden">
          {/* Hero Image */}
          <div className="relative h-64 sm:h-80 bg-gray-100">
            {popup.thumbnail_url ? (
              <img
                src={popup.thumbnail_url}
                alt={popup.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <MapPin className="h-16 w-16 text-gray-300" />
              </div>
            )}

            {/* Status Badge */}
            <div className="absolute top-4 right-4">
              {popup.is_active ? (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-500 text-white text-sm font-medium">
                  <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                  {t.ongoing}
                </span>
              ) : (
                <span className="px-3 py-1.5 rounded-full bg-gray-500 text-white text-sm font-medium">
                  {t.ended}
                </span>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 sm:p-8">
            {/* Header */}
            <div className="mb-6">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <CategoryBadge category={popup.category} className="mb-3" />
                  <h1 className="text-2xl font-bold text-gray-900 mb-1">
                    {popup.name_korean}
                  </h1>
                  {popup.name !== popup.name_korean && (
                    <p className="text-lg text-gray-500">{popup.name}</p>
                  )}
                </div>
              </div>

              <p className="text-gray-600 text-sm">
                {popup.brand}
              </p>
            </div>

            {/* Tags */}
            {popup.tags && popup.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {popup.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2.5 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            )}

            {/* Info Grid */}
            <div className="grid sm:grid-cols-2 gap-4 mb-8">
              {/* Period */}
              <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl">
                <Calendar className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{t.period}</p>
                  <p className="text-sm text-gray-600">
                    {formatDateRange(popup.period_start, popup.period_end)}
                  </p>
                </div>
              </div>

              {/* Hours */}
              <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl">
                <Clock className="h-5 w-5 text-gray-400 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{t.hours}</p>
                  <p className="text-sm text-gray-600">{popup.operating_hours}</p>
                </div>
              </div>

              {/* Location */}
              <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl sm:col-span-2">
                <MapPin className="h-5 w-5 text-gray-400 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{t.location}</p>
                  <p className="text-sm text-gray-600">{popup.address}</p>
                </div>
              </div>
            </div>

            {/* Description */}
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">{t.about}</h2>
              <p className="text-gray-600 leading-relaxed">
                {getDescription()}
              </p>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3">
              <a
                href={naverMapUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-green-500 text-white font-medium rounded-lg hover:bg-green-600 transition-colors"
              >
                <Navigation className="h-4 w-4" />
                {t.naverMap}
              </a>

              <a
                href={googleMapUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-500 text-white font-medium rounded-lg hover:bg-blue-600 transition-colors"
              >
                <ExternalLink className="h-4 w-4" />
                {t.googleMaps}
              </a>

              {popup.source_post_url && (
                <a
                  href={popup.source_post_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <Instagram className="h-4 w-4" />
                  Instagram
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
