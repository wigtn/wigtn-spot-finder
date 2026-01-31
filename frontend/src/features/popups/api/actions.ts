"use server";

import type { PopupStore, PopupSummary, PopupCategory } from "@/types";
import { SAMPLE_POPUPS, filterPopups, getPopupById as getPopupByIdFromData } from "@/lib/popup-data";

export interface GetPopupsParams {
  category?: PopupCategory;
  search?: string;
  active_only?: boolean;
  page?: number;
  limit?: number;
}

export async function getPopups(params: GetPopupsParams = {}): Promise<{
  data: PopupSummary[];
  total: number;
}> {
  // Use real popup data from popup-data.ts
  const filtered = filterPopups({
    category: params.category,
    search: params.search,
    activeOnly: params.active_only,
  });

  const summaries: PopupSummary[] = filtered.map((p) => ({
    id: p.id,
    name: p.name,
    name_korean: p.name_korean,
    category: p.category,
    location: p.location,
    period_start: p.period_start,
    period_end: p.period_end,
    thumbnail_url: p.thumbnail_url,
    is_active: p.is_active,
  }));

  return { data: summaries, total: summaries.length };
}

export async function getPopupById(id: string): Promise<PopupStore | null> {
  return getPopupByIdFromData(id);
}

export async function getPopupCategories(): Promise<{ category: PopupCategory; count: number }[]> {
  const categories = new Map<PopupCategory, number>();
  SAMPLE_POPUPS.forEach((p) => {
    categories.set(p.category, (categories.get(p.category) || 0) + 1);
  });

  return Array.from(categories.entries()).map(([category, count]) => ({
    category,
    count,
  }));
}
