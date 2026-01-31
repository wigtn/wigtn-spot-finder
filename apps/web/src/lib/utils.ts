import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: Date | string, locale: string = "ko") {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleDateString(locale === "ko" ? "ko-KR" : locale === "ja" ? "ja-JP" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateRange(start: Date | string, end: Date | string, locale: string = "ko") {
  return `${formatDate(start, locale)} - ${formatDate(end, locale)}`;
}
