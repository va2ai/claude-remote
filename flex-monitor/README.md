# Flex Monitor

Expo (React Native) mobile app for monitoring Amazon Flex delivery offers with push notifications.

## Features

- **Token Entry** — Paste tokens captured from mitmproxy
- **Region Selection** — North America, Europe, Far East
- **Service Area Config** — Choose which areas to monitor
- **Live Polling** — Start/stop monitoring with rate-limited requests
- **Background Fetch** — Polls ~every 15 minutes when app is minimized (iOS minimum)
- **Push Notifications** — Alerts when new offers are found
- **Secure Storage** — Tokens stored in device keychain via `expo-secure-store`

## Prerequisites

- Node.js v18+
- [Expo Go](https://expo.dev/go) on your iPhone or Android device
- Amazon Flex access token (captured via mitmproxy)

## Setup

```bash
cd flex-monitor
npm install
npx expo start
```

Scan the QR code with Expo Go on your phone.

## Getting Your Token

1. Set up mitmproxy on your computer
2. Configure your phone to proxy through mitmproxy
3. Open the Amazon Flex app and navigate around
4. Look for requests to `flex-capacity-*.amazon.com`
5. Copy the `x-amz-access-token` header value
6. Paste it into the app's Login screen

## Auto-Loading Tokens

Create `src/constants/defaultTokens.js` to auto-load tokens on first launch:

```js
export const DEFAULT_TOKENS = {
  access_token: 'your-access-token-here',
  refresh_token: 'your-refresh-token-here',
};
```

This file is gitignored and won't be committed.

## Project Structure

```
flex-monitor/
├── App.js                         # Navigation + background fetch
├── app.json                       # Expo config
└── src/
    ├── constants/
    │   └── config.js              # Regions, rate limits, storage keys
    ├── hooks/
    │   ├── useAuth.js             # Token management
    │   └── useOffers.js           # Polling logic
    ├── screens/
    │   ├── LoginScreen.js         # Token entry
    │   ├── DashboardScreen.js     # Main monitoring UI
    │   └── SettingsScreen.js      # Settings & logout
    ├── services/
    │   └── flexApi.js             # Amazon Flex API calls
    └── utils/
        └── storage.js             # SecureStore wrapper
```

## Notes

- No Apple Developer account needed when testing with Expo Go
- Background fetch is limited to ~15 minute intervals on iOS
- Rate limiting mirrors the Node.js scraper (30-60s polling, backoff on 400/420)

## Disclaimer

This project is for **educational and research purposes only**. Amazon Flex does not provide an official public API. Automated access may violate Amazon's Terms of Service and could result in account deactivation. Use at your own risk.

## License

MIT
