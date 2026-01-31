"use client";

import Link from "next/link";
import { MapPin, MessageCircle, Grid3X3, ArrowRight, Sparkles } from "lucide-react";
import { useLanguage } from "@/contexts/language-context";
import { LANGUAGES } from "@/types";
import { cn } from "@/lib/utils";
import type { Language } from "@/types";

const content: Record<Language, {
  badge: string;
  heroTitle1: string;
  heroTitle2: string;
  heroDesc: string;
  browseBtn: string;
  chatBtn: string;
  featuresTitle: string;
  featuresDesc: string;
  feature1Title: string;
  feature1Desc: string;
  feature1Link: string;
  feature2Title: string;
  feature2Desc: string;
  feature2Link: string;
  feature3Title: string;
  feature3Desc: string;
  feature3Link: string;
  ctaTitle: string;
  ctaDesc: string;
  ctaBtn: string;
}> = {
  ja: {
    badge: "AIポップアップストアガイド",
    heroTitle1: "聖水洞のポップアップストアを",
    heroTitle2: "スマートに探検しよう",
    heroDesc: "外国人旅行者のためのAIガイド。リアルタイムポップアップストア情報とカスタム旅行プランを一目で確認。",
    browseBtn: "ポップアップを見る",
    chatBtn: "AIとチャット",
    featuresTitle: "すべての機能を一箇所で",
    featuresDesc: "ポップアップストア検索、AIチャット、マップ - 旅行に必要なすべて",
    feature1Title: "ポップアップギャラリー",
    feature1Desc: "聖水洞の最新ポップアップストアをカテゴリー別に探索。ファッション、ビューティー、F&Bなど様々なブランドに出会えます。",
    feature1Link: "見てみる",
    feature2Title: "AI旅行ガイド",
    feature2Desc: "AIと会話しながらカスタム旅行プランを作成。日本語、英語、韓国語でコミュニケーション可能。",
    feature2Link: "チャット開始",
    feature3Title: "インタラクティブマップ",
    feature3Desc: "地図でポップアップストアの位置を確認し、近くから効率的に訪問しましょう。",
    feature3Link: "マップを見る",
    ctaTitle: "今すぐ始めましょう",
    ctaDesc: "ログインなしでもすべての機能をご利用いただけます。",
    ctaBtn: "始める",
  },
  en: {
    badge: "AI Popup Store Guide",
    heroTitle1: "Explore Seongsu-dong",
    heroTitle2: "Popup Stores Smartly",
    heroDesc: "AI guide for international travelers. Check real-time popup store info and custom travel itineraries at a glance.",
    browseBtn: "Browse Popups",
    chatBtn: "Chat with AI",
    featuresTitle: "All features in one place",
    featuresDesc: "Popup store search, AI chat, maps - everything you need for travel",
    feature1Title: "Popup Gallery",
    feature1Desc: "Explore the latest popup stores in Seongsu-dong by category. Meet various brands in fashion, beauty, F&B and more.",
    feature1Link: "Browse",
    feature2Title: "AI Travel Guide",
    feature2Desc: "Plan custom travel itineraries while chatting with AI. Available in Japanese, English, and Korean.",
    feature2Link: "Start Chat",
    feature3Title: "Interactive Map",
    feature3Desc: "Check popup store locations on the map and visit efficiently starting from nearby ones.",
    feature3Link: "View Map",
    ctaTitle: "Get started now",
    ctaDesc: "Use all features without signing in.",
    ctaBtn: "Get Started",
  },
  ko: {
    badge: "AI 기반 팝업스토어 가이드",
    heroTitle1: "성수동 팝업스토어를",
    heroTitle2: "스마트하게 탐험하세요",
    heroDesc: "외국인 여행자를 위한 AI 가이드. 실시간 팝업스토어 정보와 맞춤형 여행 일정을 한눈에 확인하세요.",
    browseBtn: "팝업스토어 둘러보기",
    chatBtn: "AI와 대화하기",
    featuresTitle: "모든 기능을 한 곳에서",
    featuresDesc: "팝업스토어 탐색, AI 채팅, 지도 - 여행에 필요한 모든 것",
    feature1Title: "팝업스토어 갤러리",
    feature1Desc: "성수동의 최신 팝업스토어를 카테고리별로 탐색하세요. 패션, 뷰티, F&B 등 다양한 브랜드를 만나보세요.",
    feature1Link: "둘러보기",
    feature2Title: "AI 여행 가이드",
    feature2Desc: "AI와 대화하며 맞춤형 여행 일정을 계획하세요. 영어, 일본어, 한국어로 소통 가능합니다.",
    feature2Link: "대화 시작",
    feature3Title: "인터랙티브 지도",
    feature3Desc: "지도에서 팝업스토어 위치를 확인하고, 가까운 곳부터 효율적으로 방문하세요.",
    feature3Link: "지도 보기",
    ctaTitle: "지금 바로 시작하세요",
    ctaDesc: "로그인 없이도 모든 기능을 이용할 수 있습니다.",
    ctaBtn: "시작하기",
  },
};

export default function HomePage() {
  const { language, setLanguage } = useLanguage();
  const t = content[language];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary-600 via-primary-700 to-accent-700">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />

        {/* Language Selector - Top Right */}
        <div className="absolute top-4 right-4 z-20 flex items-center gap-1 bg-white/10 backdrop-blur-sm rounded-lg p-1">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => setLanguage(lang.code)}
              className={cn(
                "px-3 py-1.5 text-sm font-medium rounded-md transition-all",
                language === lang.code
                  ? "bg-white text-primary-700 shadow-sm"
                  : "text-white/80 hover:text-white hover:bg-white/10"
              )}
            >
              {lang.shortLabel}
            </button>
          ))}
        </div>

        <div className="relative mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-white/90 text-sm mb-6">
              <Sparkles className="h-4 w-4" />
              {t.badge}
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
              {t.heroTitle1}
              <br />
              <span className="text-primary-200">{t.heroTitle2}</span>
            </h1>
            <p className="mt-6 max-w-2xl mx-auto text-lg text-primary-100">
              {t.heroDesc}
            </p>
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/popups"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-white text-primary-700 font-medium hover:bg-primary-50 transition-colors"
              >
                {t.browseBtn}
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/chat"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-white/30 text-white font-medium hover:bg-white/10 transition-colors"
              >
                <MessageCircle className="h-4 w-4" />
                {t.chatBtn}
              </Link>
            </div>
          </div>
        </div>

        {/* Wave divider */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg
            viewBox="0 0 1440 120"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="w-full h-auto"
          >
            <path
              d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0Z"
              fill="#f9fafb"
            />
          </svg>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-gray-50">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
              {t.featuresTitle}
            </h2>
            <p className="mt-4 text-lg text-gray-600">
              {t.featuresDesc}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <Link
              href="/popups"
              className="group p-8 bg-white rounded-2xl border border-gray-200 hover:border-primary-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="h-12 w-12 rounded-xl bg-pink-100 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <Grid3X3 className="h-6 w-6 text-pink-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {t.feature1Title}
              </h3>
              <p className="text-gray-600 mb-4">
                {t.feature1Desc}
              </p>
              <span className="inline-flex items-center gap-1 text-primary-600 font-medium group-hover:gap-2 transition-all">
                {t.feature1Link} <ArrowRight className="h-4 w-4" />
              </span>
            </Link>

            {/* Feature 2 */}
            <Link
              href="/chat"
              className="group p-8 bg-white rounded-2xl border border-gray-200 hover:border-primary-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="h-12 w-12 rounded-xl bg-primary-100 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <MessageCircle className="h-6 w-6 text-primary-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {t.feature2Title}
              </h3>
              <p className="text-gray-600 mb-4">
                {t.feature2Desc}
              </p>
              <span className="inline-flex items-center gap-1 text-primary-600 font-medium group-hover:gap-2 transition-all">
                {t.feature2Link} <ArrowRight className="h-4 w-4" />
              </span>
            </Link>

            {/* Feature 3 */}
            <Link
              href="/map"
              className="group p-8 bg-white rounded-2xl border border-gray-200 hover:border-primary-300 hover:shadow-lg transition-all duration-200"
            >
              <div className="h-12 w-12 rounded-xl bg-teal-100 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <MapPin className="h-6 w-6 text-teal-600" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-3">
                {t.feature3Title}
              </h3>
              <p className="text-gray-600 mb-4">
                {t.feature3Desc}
              </p>
              <span className="inline-flex items-center gap-1 text-primary-600 font-medium group-hover:gap-2 transition-all">
                {t.feature3Link} <ArrowRight className="h-4 w-4" />
              </span>
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-white border-t border-gray-100">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            {t.ctaTitle}
          </h2>
          <p className="text-gray-600 mb-8">
            {t.ctaDesc}
          </p>
          <Link
            href="/popups"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 transition-colors"
          >
            {t.ctaBtn}
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-gray-900 text-gray-400">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-primary-400" />
              <span className="font-semibold text-white">Spotfinder</span>
            </div>
            <p className="text-sm">
              © 2024 Spotfinder. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
