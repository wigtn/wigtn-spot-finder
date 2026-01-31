"use client";

import { useState, useEffect } from "react";
import { MapView } from "@/features/map/components/map-view";
import { CategoryFilter } from "@/features/popups/components";
import { SAMPLE_POPUPS } from "@/lib/popup-data";
import type { PopupStore, PopupCategory } from "@/types";

export default function MapPage() {
  const [popups, setPopups] = useState<PopupStore[]>([]);
  const [selectedPopup, setSelectedPopup] = useState<PopupStore | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<PopupCategory | null>(null);

  useEffect(() => {
    let filtered = [...SAMPLE_POPUPS];
    if (selectedCategory) {
      filtered = filtered.filter((p) => p.category === selectedCategory);
    }
    setPopups(filtered);
  }, [selectedCategory]);

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Filter Bar */}
      <div className="px-4 py-3 bg-white border-b border-gray-200 overflow-x-auto">
        <CategoryFilter
          selected={selectedCategory}
          onSelect={setSelectedCategory}
        />
      </div>

      {/* Map */}
      <div className="flex-1 overflow-hidden">
        <MapView
          popups={popups}
          selectedPopup={selectedPopup}
          onPopupClick={(popup) => setSelectedPopup(popup)}
        />
      </div>
    </div>
  );
}
