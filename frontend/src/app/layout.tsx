import type { Metadata } from "next";
import "./globals.css";
import { LanguageProvider } from "@/contexts/language-context";

export const metadata: Metadata = {
  title: "Spotfinder - 聖水洞ポップアップストアガイド",
  description: "外国人旅行者のためのAIポップアップストアガイド。聖水洞のホットなポップアップストアを見つけましょう。",
  keywords: ["ポップアップストア", "聖水洞", "ソウル", "旅行", "popup store", "seongsu", "성수동"],
  openGraph: {
    title: "Spotfinder - 聖水洞ポップアップストアガイド",
    description: "外国人旅行者のためのAIポップアップストアガイド",
    type: "website",
    locale: "ja_JP",
    alternateLocale: ["en_US", "ko_KR"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <head>
        <link
          rel="stylesheet"
          as="style"
          crossOrigin="anonymous"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
      </head>
      <body className="antialiased bg-gray-50 text-gray-900 min-h-screen">
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
