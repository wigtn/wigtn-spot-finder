# Spotfinder Mobile App

React Native (Expo) mobile application for discovering popup stores in Seongsu-dong.

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm start

# Run on iOS
npm run ios

# Run on Android
npm run android
```

## Project Structure

```
apps/mobile/
├── app/              # Expo Router pages
│   ├── (tabs)/       # Tab navigation
│   ├── popup/        # Popup detail screens
│   └── _layout.tsx   # Root layout
├── components/       # Shared components
├── hooks/           # Custom hooks
├── services/        # API services
├── types/           # TypeScript types
└── assets/          # Images, fonts
```

## Features

- Popup store discovery
- AI chat assistant
- Map integration
- Multi-language support (JP/EN/KO)
