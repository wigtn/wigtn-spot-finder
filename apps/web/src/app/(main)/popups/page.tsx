"use client";

import { useState, useEffect } from "react";
import { Search } from "lucide-react";
import { Input } from "@/components/ui";
import { PopupGrid, CategoryFilter } from "@/features/popups/components";
import { getPopups } from "@/features/popups/api/actions";
import { useLanguage } from "@/contexts/language-context";
import type { PopupSummary, PopupCategory, Language } from "@/types";

const pageContent: Record<Language, {
  title: string;
  subtitle: string;
  searchPlaceholder: string;
}> = {
  ja: {
    title: "聖水洞ポップアップストア",
    subtitle: "現在開催中のポップアップストアをご覧ください",
    searchPlaceholder: "ポップアップストアを検索...",
  },
  en: {
    title: "Seongsu-dong Popup Stores",
    subtitle: "Browse currently active popup stores",
    searchPlaceholder: "Search popup stores...",
  },
  ko: {
    title: "성수동 팝업스토어",
    subtitle: "지금 진행 중인 팝업스토어를 둘러보세요",
    searchPlaceholder: "팝업스토어 검색...",
  },
};

export default function PopupsPage() {
  const { language } = useLanguage();
  const t = pageContent[language];

  const [popups, setPopups] = useState<PopupSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<PopupCategory | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch popups
  useEffect(() => {
    const fetchPopups = async () => {
      setLoading(true);
      const { data } = await getPopups({
        category: selectedCategory || undefined,
        search: debouncedSearch || undefined,
        active_only: true,
      });
      setPopups(data);
      setLoading(false);
    };

    fetchPopups();
  }, [selectedCategory, debouncedSearch]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {t.title}
          </h1>
          <p className="text-gray-600 mb-6">
            {t.subtitle}
          </p>

          {/* Search */}
          <div className="mb-6 max-w-md">
            <Input
              type="search"
              placeholder={t.searchPlaceholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
            />
          </div>

          {/* Category Filter */}
          <CategoryFilter
            selected={selectedCategory}
            onSelect={setSelectedCategory}
          />
        </div>
      </div>

      {/* Grid */}
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <PopupGrid popups={popups} loading={loading} />
      </div>
    </div>
  );
}
