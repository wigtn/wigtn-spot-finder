// Popup Store Types
export type PopupCategory =
  | "fashion"
  | "cafe"
  | "art"
  | "cosmetics"
  | "food"
  | "lifestyle"
  | "entertainment"
  | "collaboration"
  | "other";

export interface PopupStore {
  id: string;
  name: string;
  name_korean: string;
  brand: string;
  category: PopupCategory;
  tags: string[];
  location: string;
  address: string;
  coordinates: {
    longitude: number;
    latitude: number;
  };
  period_start: string;
  period_end: string;
  operating_hours: string;
  description: string;
  description_ja?: string;
  description_en?: string;
  images: string[];
  thumbnail_url: string;
  source_post_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PopupSummary {
  id: string;
  name: string;
  name_korean: string;
  category: PopupCategory;
  location: string;
  period_start: string;
  period_end: string;
  thumbnail_url: string;
  is_active: boolean;
}

// Chat Popup Card - lightweight popup data for chat display
export interface ChatPopupCard {
  id: string;
  name: string;
  name_korean: string | null;
  category: PopupCategory;
  location: string;
  period_start: string | null;
  period_end: string | null;
  thumbnail_url: string | null;
  is_active: boolean;
}

// Chat Types
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  thread_id?: string;
  user_id?: string;
  language?: "en" | "ja" | "ko";
}

export interface ChatResponse {
  response: string;
  thread_id: string;
  turn_number: number;
  stage: "init" | "investigation" | "planning" | "resolution";
  latency_ms: number;
  timestamp: string;
}

// User Types
export interface User {
  id: string;
  email: string;
  user_metadata: {
    full_name?: string;
    avatar_url?: string;
  };
}

// Language - Japanese first (main target audience)
export type Language = "ja" | "en" | "ko";

export const LANGUAGES: { code: Language; label: string; shortLabel: string }[] = [
  { code: "ja", label: "日本語", shortLabel: "JP" },
  { code: "en", label: "English", shortLabel: "EN" },
  { code: "ko", label: "한국어", shortLabel: "KR" },
];

export const DEFAULT_LANGUAGE: Language = "ja";

// Navigation labels by language
export const NAV_LABELS: Record<Language, { popups: string; chat: string; map: string }> = {
  ja: { popups: "ポップアップ", chat: "チャット", map: "マップ" },
  en: { popups: "Popups", chat: "Chat", map: "Map" },
  ko: { popups: "팝업", chat: "채팅", map: "지도" },
};

// Category Colors
export const CATEGORY_COLORS: Record<PopupCategory, { bg: string; text: string }> = {
  fashion: { bg: "bg-pink-100", text: "text-pink-700" },
  cafe: { bg: "bg-amber-100", text: "text-amber-700" },
  art: { bg: "bg-purple-100", text: "text-purple-700" },
  cosmetics: { bg: "bg-rose-100", text: "text-rose-700" },
  food: { bg: "bg-orange-100", text: "text-orange-700" },
  lifestyle: { bg: "bg-teal-100", text: "text-teal-700" },
  entertainment: { bg: "bg-indigo-100", text: "text-indigo-700" },
  collaboration: { bg: "bg-cyan-100", text: "text-cyan-700" },
  other: { bg: "bg-gray-100", text: "text-gray-700" },
};
