# claude-remote

Amazon Flex tooling — scraper and mobile monitor app.

## Projects

### [amazon-flex-scraper](./amazon-flex-scraper/)

Node.js tool that polls for Amazon Flex delivery blocks via the internal API. Runs on a server or local machine with rate-limiting safeguards.

- Polls `GetOffersForProviderPost` on a configurable interval
- Exponential backoff on rate-limit responses
- Logs found offers to `offers.log`

### [flex-monitor](./flex-monitor/)

Expo (React Native) mobile app for iOS/Android that monitors Flex offers and sends push notifications.

- Secure token storage via device keychain
- Foreground polling with start/stop controls
- Background fetch (~15 min intervals on iOS)
- Push notifications when offers are found
- Region selection (NA, EU, Far East)
- Service area configuration

## Getting Started

```bash
git clone https://github.com/va2ai/claude-remote.git
cd claude-remote

# Run the scraper
cd amazon-flex-scraper && npm install && npm start

# Run the mobile app
cd flex-monitor && npm install && npx expo start
```

Both tools require Amazon Flex authentication tokens captured via mitmproxy from the Flex mobile app.

## License

MIT
