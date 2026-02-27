# Amazon Flex API Research

## Overview

Amazon does **not** provide an official public API for Amazon Flex. All known API interaction methods are based on **reverse-engineering** the mobile app's network traffic using tools like Charles Proxy or mitmproxy. Using these unofficial APIs may violate Amazon's Terms of Service and could result in account deactivation.

---

## Key GitHub Repositories

### 1. [mdesilva/AmazonFlexUnlimited](https://github.com/mdesilva/AmazonFlexUnlimited) (Most Popular)
- **Language:** Python 3
- **Approach:** Reverse-engineered API via Charles Proxy on iOS
- **Features:** Automated block grabbing, SMS notifications via Twilio
- **Note:** Does not work from AWS data centers (Amazon blocks DC IPs)

### 2. [cyleleghorn/AmazonFlexChecker](https://github.com/cyleleghorn/AmazonFlexChecker)
- Checks Amazon Flex for available time blocks
- Planned Android companion app

### 3. [lumo93/RE-FLEX](https://github.com/lumo93/RE-FLEX)
- **Status:** Abandoned / Not functional
- Modular design with separate auth, request, and header modules
- Spoofs Android Flex app User-Agent (e.g., version `3.96.2.61.0`)
- Includes device attestation and cryptographic signature headers

### 4. [CuzaCutuza/AmazonFlexWorker](https://github.com/CuzaCutuza/AmazonFlexWorker)
- **Language:** Python
- Automates driver job pickups
- Requires anti-CAPTCHA token API for challenge completion

### 5. [akary-ackett/amazon-flex-api-instant-offer-bot](https://github.com/akary-ackett/amazon-flex-api-instant-offer-bot)
- **Language:** JavaScript / Node.js
- **Stack:** Express, AWS SDK, Puppeteer, Axios
- Fetches and auto-accepts instant offers

---

## Reverse-Engineered API Details

### Base URLs

| Endpoint | URL |
|----------|-----|
| Get Offers | `https://flex-capacity-na.amazon.com/GetOffersForProviderPost` |
| Accept Offer | `https://flex-capacity-na.amazon.com/AcceptOffer` |
| Forfeit Offer | `https://flex-capacity-na.amazon.com/schedule/blocks/` |
| Get Eligible Service Areas | `https://flex-capacity-na.amazon.com/eligibleServiceAreas` |
| Get Offer Filter Options | `https://flex-capacity-na.amazon.com/getOfferFiltersOptions` |
| Auth Registration | `https://api.amazon.com/auth/register` |
| Token Refresh | `https://api.amazon.com/auth/token` |

> **Note:** The `na` in the URL stands for North America. Other regions likely have different subdomains (e.g., `flex-capacity-eu.amazon.com`).

### Authentication Flow

1. **Initial OAuth Login:**
   - User manually opens an Amazon login URL in their browser
   - Signs in with Amazon Flex credentials
   - Gets redirected to a URL containing an access code (the "maplanding" URL)
   - The code is extracted from the redirect URL

2. **Token Registration:**
   ```
   POST https://api.amazon.com/auth/register
   ```
   - Exchanges the OAuth code for an access token and a refresh token

3. **Token Refresh:**
   ```
   POST https://api.amazon.com/auth/token
   ```
   ```json
   {
     "source_token_type": "refresh_token",
     "source_token": "<REFRESH_TOKEN>",
     "requested_token_type": "access_token"
   }
   ```
   - Returns a new access token when the current one expires

### Request Headers

```
Accept: application/json
Content-Type: application/json
x-amz-access-token: <ACCESS_TOKEN>
X-Amz-Date: <TIMESTAMP>
User-Agent: iOS/16.1 (iPhone Darwin) Model/iPhone...
```

Some implementations also include:
- Custom signature headers for request authentication
- Device attestation tokens

### Get Offers Request Payload

```json
{
  "apiVersion": "V2",
  "filters": {
    "serviceAreaFilter": ["<WAREHOUSE_IDS>"],
    "timeFilter": {
      "endTime": "<ISO_TIMESTAMP>",
      "startTime": "<ISO_TIMESTAMP>"
    }
  },
  "serviceAreaIds": ["<SERVICE_AREA_IDS>"]
}
```

### Error Handling & Rate Limiting

- **400 responses:** Trigger a 30-minute cooldown (likely CAPTCHA challenge or throttle)
- **Exponential backoff:** Up to 4 retry attempts
- **Configurable parameters:** `retryLimit`, `refreshInterval` (seconds between requests)

---

## Reverse Engineering Methodology

The common approach used across all projects:

1. **Install a MITM proxy** (Charles Proxy or mitmproxy)
2. **Configure the mobile device** to route traffic through the proxy
3. **Install the proxy's CA certificate** on the device
4. **Use the Amazon Flex app** while capturing traffic (login, search, accept/decline offers)
5. **Analyze captured requests** to identify endpoints, headers, and payloads

### Useful Tool

- [mitmproxy2swagger](https://github.com/alufers/mitmproxy2swagger) - Automatically converts mitmproxy captures to OpenAPI 3.0 specs, making it easier to document reverse-engineered APIs.

---

## Key Challenges

1. **Authentication complexity:** Amazon uses OAuth 2.0 with device attestation and cryptographic signatures
2. **CAPTCHA challenges:** Amazon may require CAPTCHA verification, necessitating anti-CAPTCHA services
3. **IP blocking:** Amazon blocks requests from known data center IP ranges (AWS, GCP, etc.)
4. **API changes:** Amazon frequently updates the app and API, breaking reverse-engineered integrations
5. **Account risk:** Automated access violates Amazon's ToS and can result in permanent account deactivation

---

## Disclaimer

This research is for **educational and informational purposes only**. The Amazon Flex API is not publicly documented, and accessing it programmatically outside of the official app may violate Amazon's Terms of Service. Use this information at your own risk.
