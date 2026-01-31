"use client";

import { cn } from "@/lib/utils";
import { useLanguage } from "@/contexts/language-context";
import type { PopupCategory, Language } from "@/types";
import { CATEGORY_COLORS } from "@/types";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "outline";
  className?: string;
}

export function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        variant === "default" && "bg-gray-100 text-gray-700",
        variant === "outline" && "border border-gray-300 text-gray-600",
        className
      )}
    >
      {children}
    </span>
  );
}

interface CategoryBadgeProps {
  category: PopupCategory;
  className?: string;
}

const categoryLabels: Record<Language, Record<PopupCategory, string>> = {
  ja: {
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

export function CategoryBadge({ category, className }: CategoryBadgeProps) {
  const { language } = useLanguage();
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.other;
  const labels = categoryLabels[language];

  return (
    <span
      className={cn(
        "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
        colors.bg,
        colors.text,
        className
      )}
    >
      {labels[category]}
    </span>
  );
}
