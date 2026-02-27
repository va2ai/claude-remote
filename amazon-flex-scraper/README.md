# Amazon Flex Scraper

A Node.js tool for scraping Amazon Flex delivery block data.

## Prerequisites

- Node.js (v18 or higher recommended)

## Installation

```bash
cd amazon-flex-scraper
npm install
```

## Usage

```bash
# Start the scraper
npm start

# Start in development mode (auto-reload on file changes)
npm run dev
```

## Project Structure

```
amazon-flex-scraper/
├── package.json
├── README.md
└── src/
    └── index.js        # Entry point
```

## How It Works

The scraper interacts with Amazon Flex's internal API, which was reverse-engineered from the mobile app's network traffic. Key aspects:

### API Endpoints

| Endpoint | URL |
|----------|-----|
| Get Offers | `https://flex-capacity-na.amazon.com/GetOffersForProviderPost` |
| Accept Offer | `https://flex-capacity-na.amazon.com/AcceptOffer` |
| Forfeit Offer | `https://flex-capacity-na.amazon.com/schedule/blocks/` |
| Service Areas | `https://flex-capacity-na.amazon.com/eligibleServiceAreas` |
| Offer Filters | `https://flex-capacity-na.amazon.com/getOfferFiltersOptions` |

> The `na` subdomain is for North America. Other regions use different subdomains (e.g., `flex-capacity-eu.amazon.com`).

### Authentication

Amazon Flex uses OAuth 2.0 with the following flow:

1. Open the Amazon login URL in a browser and sign in with Flex credentials
2. Extract the access code from the redirect URL (the "maplanding" URL)
3. Exchange the code for access and refresh tokens via `POST https://api.amazon.com/auth/register`
4. Refresh expired tokens via `POST https://api.amazon.com/auth/token`

### Request Format

Requests require these headers:

```
Accept: application/json
Content-Type: application/json
x-amz-access-token: <ACCESS_TOKEN>
X-Amz-Date: <TIMESTAMP>
User-Agent: <FLEX_APP_USER_AGENT>
```

### Rate Limiting

- 400 responses trigger a ~30-minute cooldown
- Exponential backoff is recommended (up to 4 retries)
- Requests from data center IPs (AWS, GCP, etc.) are blocked by Amazon

## Related Research

See [amazon-flex-api-research.md](../amazon-flex-api-research.md) for detailed API research, including a full list of reference repositories and the reverse-engineering methodology.

## Disclaimer

This project is for **educational and research purposes only**. Amazon Flex does not provide an official public API. Automated access to Amazon Flex may violate Amazon's Terms of Service and could result in account deactivation. Use at your own risk.

## License

MIT
