"use client";

import { MapPin, ExternalLink, Navigation } from "lucide-react";
import { Card } from "@/components/ui";
import { CategoryBadge } from "@/components/ui/badge";
import { formatDateRange } from "@/lib/utils";
import { useLanguage } from "@/contexts/language-context";
import type { PopupStore } from "@/types";
import type { Language } from "@/types";

interface MapViewProps {
  popups: PopupStore[];
  onPopupClick?: (popup: PopupStore) => void;
  selectedPopup?: PopupStore | null;
}

const labels: Record<Language, {
  listTitle: string;
  count: string;
  legendTitle: string;
  legendDesc: string;
  naverMap: string;
  googleMaps: string;
}> = {
  ja: {
    listTitle: "ポップアップストア一覧",
    count: "件",
    legendTitle: "聖水洞ポップアップストア",
    legendDesc: "クリックして詳細を見る",
    naverMap: "Naverマップ",
    googleMaps: "Google Maps",
  },
  en: {
    listTitle: "Popup Store List",
    count: " stores",
    legendTitle: "Seongsu-dong Popup Stores",
    legendDesc: "Click to view details",
    naverMap: "Naver Map",
    googleMaps: "Google Maps",
  },
  ko: {
    listTitle: "팝업스토어 목록",
    count: "개",
    legendTitle: "성수동 팝업스토어",
    legendDesc: "클릭하여 상세보기",
    naverMap: "네이버 지도",
    googleMaps: "Google Maps",
  },
};

// Seongsu-dong center
const SEONGSU_CENTER = { lat: 37.5445, lng: 127.0565 };

export function MapView({ popups, onPopupClick, selectedPopup }: MapViewProps) {
  const { language } = useLanguage();
  const t = labels[language];

  // Get localized description
  const getDescription = (popup: PopupStore) => {
    if (language === "ja" && popup.description_ja) return popup.description_ja;
    if (language === "en" && popup.description_en) return popup.description_en;
    return popup.description;
  };

  // OpenStreetMap embed URL with markers
  const getMapUrl = (popup?: PopupStore | null) => {
    if (popup?.coordinates) {
      const { latitude, longitude } = popup.coordinates;
      return `https://www.openstreetmap.org/export/embed.html?bbox=${longitude - 0.005}%2C${latitude - 0.003}%2C${longitude + 0.005}%2C${latitude + 0.003}&layer=mapnik&marker=${latitude}%2C${longitude}`;
    }
    // Default: Seongsu-dong area
    return `https://www.openstreetmap.org/export/embed.html?bbox=127.0465%2C37.5395%2C127.0665%2C37.5495&layer=mapnik`;
  };

  const getNaverMapUrl = (popup: PopupStore) => {
    return `https://map.naver.com/v5/search/${encodeURIComponent(popup.address || popup.location)}`;
  };

  const getGoogleMapsUrl = (popup: PopupStore) => {
    if (popup.coordinates) {
      return `https://www.google.com/maps?q=${popup.coordinates.latitude},${popup.coordinates.longitude}`;
    }
    return `https://www.google.com/maps/search/${encodeURIComponent(popup.address || popup.location)}`;
  };

  return (
    <div className="flex h-full">
      {/* Popup List - Left Side */}
      <div className="w-80 h-full overflow-y-auto border-r border-gray-200 bg-white hidden md:block">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">{t.listTitle}</h3>
          <p className="text-sm text-gray-500">{popups.length}{t.count}</p>
        </div>

        <div className="divide-y divide-gray-100">
          {popups.map((popup) => (
            <button
              key={popup.id}
              onClick={() => onPopupClick?.(popup)}
              className={`w-full p-4 text-left hover:bg-gray-50 transition-colors ${
                selectedPopup?.id === popup.id ? "bg-primary-50 border-l-2 border-primary-500" : ""
              }`}
            >
              <div className="flex gap-3">
                {/* Thumbnail */}
                <div className="w-16 h-16 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0">
                  {popup.thumbnail_url ? (
                    <img
                      src={popup.thumbnail_url}
                      alt={popup.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <MapPin className="h-6 w-6 text-gray-300" />
                    </div>
                  )}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <CategoryBadge category={popup.category} className="mb-1" />
                  <h4 className="font-medium text-gray-900 truncate text-sm">
                    {popup.name}
                  </h4>
                  <p className="text-xs text-gray-500 truncate">{popup.address || popup.location}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Map Area - Right Side */}
      <div className="flex-1 relative bg-gray-100">
        {/* OpenStreetMap iframe */}
        <iframe
          src={getMapUrl(selectedPopup)}
          className="w-full h-full border-0"
          title="Map"
          loading="lazy"
          style={{ border: 0 }}
        />

        {/* Selected Popup Info Card */}
        {selectedPopup && (
          <Card className="absolute bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-10 shadow-xl">
            <div className="p-4">
              <div className="flex gap-3">
                <div className="w-20 h-20 rounded-lg bg-gray-100 overflow-hidden flex-shrink-0">
                  {selectedPopup.thumbnail_url ? (
                    <img
                      src={selectedPopup.thumbnail_url}
                      alt={selectedPopup.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <MapPin className="h-8 w-8 text-gray-300" />
                    </div>
                  )}
                </div>

                <div className="flex-1">
                  <CategoryBadge category={selectedPopup.category} className="mb-1" />
                  <h4 className="font-semibold text-gray-900">{selectedPopup.name}</h4>
                  <p className="text-sm text-gray-500 mt-1">
                    {formatDateRange(selectedPopup.period_start, selectedPopup.period_end)}
                  </p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-gray-100">
                <p className="text-sm text-gray-600 mb-2">{getDescription(selectedPopup)}</p>
                <p className="text-sm text-gray-500 mb-3">{selectedPopup.address || selectedPopup.location}</p>
                <div className="flex gap-2">
                  <a
                    href={getNaverMapUrl(selectedPopup)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 inline-flex items-center justify-center gap-1 px-3 py-2 bg-green-500 text-white text-sm font-medium rounded-lg hover:bg-green-600 transition-colors"
                  >
                    <Navigation className="h-4 w-4" />
                    {t.naverMap}
                  </a>
                  <a
                    href={getGoogleMapsUrl(selectedPopup)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 inline-flex items-center justify-center gap-1 px-3 py-2 bg-blue-500 text-white text-sm font-medium rounded-lg hover:bg-blue-600 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4" />
                    {t.googleMaps}
                  </a>
                </div>
              </div>
            </div>
          </Card>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur rounded-lg shadow-lg border border-gray-200 p-3 z-10 hidden md:block">
          <p className="text-xs font-medium text-gray-700 mb-1">{t.legendTitle}</p>
          <p className="text-xs text-gray-500">
            {popups.length}{t.count} · {t.legendDesc}
          </p>
        </div>
      </div>
    </div>
  );
}
