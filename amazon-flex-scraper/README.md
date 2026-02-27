# Amazon Flex Scraper

A Node.js tool that polls for Amazon Flex delivery blocks via the internal API with rate-limiting safeguards.

## Prerequisites

- Node.js v18+
- Python 3 + [mitmproxy](https://mitmproxy.org/) (for token capture)

## Setup

```bash
cd amazon-flex-scraper
npm install
```

## Capturing Tokens

You need authentication tokens from the Amazon Flex app. The included mitmproxy scripts capture them automatically.

### Quick Start (Windows)

```bash
# Run the helper script — shows your IP and starts mitmproxy
cd src
start-token-capture.bat
```

### Manual Setup

1. **Install mitmproxy**:
   ```bash
   pip install mitmproxy
   ```

2. **Start the capture script**:
   ```bash
   mitmdump -s src/capture-flex-tokens.py -p 8080
   ```

3. **Configure your phone**:
   - Connect to the same WiFi as your computer
   - Find your computer's local IP (`ipconfig` on Windows, `ifconfig` on Mac/Linux)
   - Go to WiFi settings > Configure proxy > Manual
   - Set proxy host to your computer's IP, port to `8080`

4. **Install the mitmproxy CA certificate**:
   - On your phone's browser, visit `http://mitm.it`
   - Download and install the certificate for your OS:
     - **iOS**: Settings > General > VPN & Device Management > Install, then Settings > General > About > Certificate Trust Settings > Enable
     - **Android**: Settings > Security > Install certificate

5. **Open the Amazon Flex app** and sign in or navigate around

6. **Tokens are saved automatically** to:
   - `.env` file (used by the scraper)
   - `src/flex-tokens.json` (JSON backup)

### Capture Scripts

| Script | Purpose |
|--------|---------|
| `src/capture-flex-tokens.py` | Captures access + refresh tokens from auth flows and API headers |
| `src/capture-headers.py` | Logs full request headers and bodies from `GetOffers` calls (for debugging) |
| `src/start-token-capture.bat` | Windows helper that shows setup instructions and starts mitmproxy |

### What Gets Captured

The token capture script watches for three sources:

1. **Auth registration** (`api.amazon.com/auth/register`) — initial sign-in flow
2. **Token refresh** (`api.amazon.com/auth/token`) — token refresh responses
3. **API request headers** (`flex-capacity-*`) — `x-amz-access-token` from any Flex API call

## Configuration

Create a `.env` file in the project root (auto-populated by the capture script):

```bash
FLEX_ACCESS_TOKEN=Atna|your-access-token-here
FLEX_REFRESH_TOKEN=Atnr|your-refresh-token-here
FLEX_REGION=na
FLEX_SERVICE_AREA_IDS=area-id-1,area-id-2
```

| Variable | Description | Default |
|----------|-------------|---------|
| `FLEX_ACCESS_TOKEN` | Amazon Flex access token (required) | — |
| `FLEX_REFRESH_TOKEN` | Refresh token for re-authentication | — |
| `FLEX_REGION` | Region: `na`, `eu`, or `fe` | `na` |
| `FLEX_SERVICE_AREA_IDS` | Comma-separated service area IDs (required) | — |

## Usage

```bash
# Start the scraper
npm start

# Start in development mode (auto-reload on file changes)
npm run dev
```

The scraper will poll for offers every 30-60 seconds and log results to the console and `offers.log`.

## API Endpoints

| Endpoint | URL |
|----------|-----|
| Get Offers | `https://flex-capacity-na.amazon.com/GetOffersForProviderPost` |
| Accept Offer | `https://flex-capacity-na.amazon.com/AcceptOffer` |
| Forfeit Offer | `https://flex-capacity-na.amazon.com/schedule/blocks/` |
| Service Areas | `https://flex-capacity-na.amazon.com/eligibleServiceAreas` |
| Offer Filters | `https://flex-capacity-na.amazon.com/getOfferFiltersOptions` |

> The `na` subdomain is for North America. Other regions: `flex-capacity-eu.amazon.com` (EU), `flex-capacity-fe.amazon.com` (Far East).

## Rate Limiting

| Parameter | Value |
|-----------|-------|
| Normal poll interval | 30-60 seconds with ±5s jitter |
| Backoff on 400/420 | 5 minutes × consecutive errors |
| Max backoff | 30 minutes |
| Request timeout | 15 seconds |

Requests from data center IPs (AWS, GCP, etc.) are blocked by Amazon — run from a residential connection.

## Project Structure

```
amazon-flex-scraper/
├── .env                           # Tokens & config (auto-generated)
├── offers.log                     # Found offers log
├── package.json
├── README.md
└── src/
    ├── index.js                   # Main scraper
    ├── capture-flex-tokens.py     # mitmproxy token capture
    ├── capture-headers.py         # mitmproxy header debugger
    └── start-token-capture.bat    # Windows capture helper
```

## Related

- [flex-monitor](../flex-monitor/) — Expo mobile app with push notifications
- [amazon-flex-api-research.md](../amazon-flex-api-research.md) — Detailed API research

## Disclaimer

This project is for **educational and research purposes only**. Amazon Flex does not provide an official public API. Automated access may violate Amazon's Terms of Service and could result in account deactivation. Use at your own risk.

## License

MIT
