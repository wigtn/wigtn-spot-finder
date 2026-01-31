# Spotfinder - 聖水洞ポップアップストアガイド

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-15-black?logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/React-19-blue?logo=react" alt="React" />
  <img src="https://img.shields.io/badge/TypeScript-5-blue?logo=typescript" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind-4-38bdf8?logo=tailwindcss" alt="Tailwind" />
</p>

외국인 관광객(특히 일본인)을 위한 AI 기반 성수동 팝업스토어 가이드 서비스입니다.

## 🌐 Live Demo

**https://frontend-blue-gamma-56.vercel.app**

## ✨ Features

- 🗺️ **팝업스토어 갤러리** - 26개 실제 성수동 팝업스토어 정보
- 💬 **AI 챗봇** - Solar Pro 2 (Upstage) 기반 여행 가이드
- 🗾 **다국어 지원** - 일본어 / 영어 / 한국어
- 🔐 **OAuth 로그인** - Google, Kakao (Supabase Auth)
- 📍 **지도 연동** - Naver Map, Google Maps 링크

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Next.js 15 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS 4 |
| Auth | Supabase SSR |
| AI/LLM | Upstage Solar Pro 2 |
| Deploy | Vercel |

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- pnpm or npm

### Installation

```bash
# Clone
git clone https://github.com/your-repo/wigtn-spot-finder.git
cd wigtn-spot-finder/frontend

# Install dependencies
npm install

# Environment variables
cp .env.example .env.local
# Edit .env.local with your Supabase credentials

# Run development server
npm run dev
```

### Environment Variables

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (main)/            # Main layout group
│   │   │   ├── popups/        # Popup list & detail
│   │   │   ├── chat/          # AI chat
│   │   │   └── map/           # Map view
│   │   └── page.tsx           # Landing page
│   ├── components/            # Reusable UI components
│   ├── contexts/              # React contexts (language)
│   ├── features/              # Feature modules
│   │   ├── chat/             # Chat feature
│   │   ├── map/              # Map feature
│   │   └── popups/           # Popups feature
│   ├── lib/                   # Utilities & data
│   └── types/                 # TypeScript types
├── public/                    # Static assets
└── tailwind.config.ts        # Tailwind configuration
```

## 🌍 Internationalization

Default language: **Japanese (日本語)**

Supported languages:
- 🇯🇵 Japanese (ja)
- 🇺🇸 English (en)
- 🇰🇷 Korean (ko)

Language selection persists in localStorage.

## 📱 Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page |
| `/popups` | Popup store gallery |
| `/popups/[id]` | Popup detail |
| `/chat` | AI travel guide chat |
| `/map` | Map view with popup locations |

## 🔗 Backend Integration

This frontend connects to the Spotfinder backend API:

- **Chat API**: `POST /api/v1/chat` - Solar Pro 2 powered responses
- **Stream API**: `POST /api/v1/chat/stream` - SSE streaming

## 📄 License

MIT License

---

Made with ❤️ for Japanese tourists visiting Seongsu-dong, Seoul
