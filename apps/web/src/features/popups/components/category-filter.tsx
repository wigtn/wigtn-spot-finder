"use client";

import { cn } from "@/lib/utils";
import { useLanguage } from "@/contexts/language-context";
import type { PopupCategory, Language } from "@/types";
import { CATEGORY_COLORS } from "@/types";

interface CategoryFilterProps {
  selected: PopupCategory | null;
  onSelect: (category: PopupCategory | null) => void;
  counts?: Record<PopupCategory, number>;
}

const categoryLabels: Record<Language, Record<PopupCategory | "all", string>> = {
  ja: {
    all: "すべて",
    fashion: "ファッション",
    cafe: "カフェ",
    art: "アート",
    cosmetics: "ビューティー",
    food: "フード",
    lifestyle: "ライフスタイル",
    entertainment: "エンタメ",
    collaboration: "コラボ",
    other: "その他",
  },
  en: {
    all: "All",
    fashion: "Fashion",
    cafe: "Cafe",
    art: "Art",
    cosmetics: "Beauty",
    food: "Food",
    lifestyle: "Lifestyle",
    entertainment: "Entertainment",
    collaboration: "Collab",
    other: "Other",
  },
  ko: {
    all: "전체",
    fashion: "패션",
    cafe: "카페",
    art: "아트",
    cosmetics: "뷰티",
    food: "푸드",
    lifestyle: "라이프스타일",
    entertainment: "엔터테인먼트",
    collaboration: "콜라보",
    other: "기타",
  },
};

const categoryKeys: (PopupCategory | null)[] = [
  null,
  "fashion",
  "cafe",
  "art",
  "cosmetics",
  "food",
  "lifestyle",
  "entertainment",
  "collaboration",
  "other",
];

export function CategoryFilter({ selected, onSelect, counts }: CategoryFilterProps) {
  const { language } = useLanguage();
  const labels = categoryLabels[language];

  return (
    <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
      {categoryKeys.map((key) => {
        const isSelected = selected === key;
        const count = key && counts ? counts[key] : undefined;
        const colors = key ? CATEGORY_COLORS[key] : null;
        const label = key ? labels[key] : labels.all;

        return (
          <button
            key={key ?? "all"}
            onClick={() => onSelect(key)}
            className={cn(
              "flex items-center gap-1.5 px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all",
              isSelected
                ? key
                  ? `${colors?.bg} ${colors?.text}`
                  : "bg-primary-600 text-white"
                : "bg-white border border-gray-200 text-gray-700 hover:border-gray-300 hover:bg-gray-50"
            )}
          >
            {label}
            {count !== undefined && (
              <span
                className={cn(
                  "text-xs px-1.5 py-0.5 rounded-full",
                  isSelected
                    ? "bg-white/20 text-current"
                    : "bg-gray-100 text-gray-500"
                )}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
