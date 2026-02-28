#!/usr/bin/env node

/**
 * Amazon Flex Scraper
 *
 * Polls for Amazon Flex delivery blocks via the internal API with
 * rate-limiting safeguards. Logs found offers to the console and offers.log.
 *
 * Usage:
 *   npm start           # run the scraper
 *   npm run dev          # run with auto-reload
 */

const { readFileSync, appendFileSync, existsSync } = require("fs");
const { resolve } = require("path");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const REGIONS = {
  na: "https://flex-capacity-na.amazon.com",
  eu: "https://flex-capacity-eu.amazon.com",
  fe: "https://flex-capacity-fe.amazon.com",
};

const AUTH_BASE = "https://api.amazon.com";

const DEFAULT_USER_AGENT =
  "iOS/16.1 (iPhone Darwin) Model/iPhone FlexApp/3.96.2.61.0";

const POLL_MIN_MS = 30000;
const POLL_MAX_MS = 60000;
const JITTER_MS = 5000;
const BACKOFF_STEP_MS = 5 * 60 * 1000; // 5 minutes
const MAX_BACKOFF_MS = 30 * 60 * 1000; // 30 minutes
const REQUEST_TIMEOUT_MS = 15000;

// ---------------------------------------------------------------------------
// Environment loading
// ---------------------------------------------------------------------------

function loadEnv() {
  const envPath = resolve(__dirname, "..", ".env");
  if (!existsSync(envPath)) return;
  const lines = readFileSync(envPath, "utf-8").split("\n");
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIdx = trimmed.indexOf("=");
    if (eqIdx === -1) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    const value = trimmed.slice(eqIdx + 1).trim();
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}

loadEnv();

function env(key, fallback) {
  return process.env[key] || fallback || "";
}

let accessToken = env("FLEX_ACCESS_TOKEN");
const REFRESH_TOKEN = env("FLEX_REFRESH_TOKEN");
const REGION = env("FLEX_REGION", "na");
const SERVICE_AREA_IDS = env("FLEX_SERVICE_AREA_IDS", "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);
const POLL_INTERVAL_MS = parseInt(env("SCRAPE_INTERVAL_MS", "0"), 10) || 0;

const BASE_URL = REGIONS[REGION] || REGIONS.na;
const LOG_PATH = resolve(__dirname, "..", "offers.log");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function amzDate() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
}

function buildHeaders() {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    "x-amz-access-token": accessToken,
    "X-Amz-Date": amzDate(),
    "User-Agent": DEFAULT_USER_AGENT,
  };
}

function isoFuture(hoursFromNow) {
  const d = new Date();
  d.setHours(d.getHours() + hoursFromNow);
  return d.toISOString();
}

function randomInterval() {
  if (POLL_INTERVAL_MS > 0) return POLL_INTERVAL_MS;
  const base = POLL_MIN_MS + Math.random() * (POLL_MAX_MS - POLL_MIN_MS);
  const jitter = (Math.random() * 2 - 1) * JITTER_MS;
  return Math.max(POLL_MIN_MS, Math.round(base + jitter));
}

function timestamp() {
  return new Date().toISOString();
}

function logToFile(message) {
  try {
    appendFileSync(LOG_PATH, `[${timestamp()}] ${message}\n`);
  } catch {
    // Ignore file write errors
  }
}

// ---------------------------------------------------------------------------
// API calls
// ---------------------------------------------------------------------------

async function fetchWithTimeout(url, opts) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  opts.signal = controller.signal;

  try {
    const res = await fetch(url, opts);
    clearTimeout(timeout);
    let data = null;
    const text = await res.text();
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    return { status: res.status, data };
  } catch (err) {
    clearTimeout(timeout);
    return { status: -1, data: null, error: err.message };
  }
}

async function refreshAccessToken() {
  if (!REFRESH_TOKEN) return false;

  console.log(`[${timestamp()}] Attempting token refresh...`);

  const { status, data } = await fetchWithTimeout(`${AUTH_BASE}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      source_token_type: "refresh_token",
      source_token: REFRESH_TOKEN,
      requested_token_type: "access_token",
    }),
  });

  if (status === 200 && data && data.access_token) {
    accessToken = data.access_token;
    console.log(`[${timestamp()}] Token refreshed successfully.`);
    logToFile("Token refreshed successfully.");
    return true;
  }

  console.error(`[${timestamp()}] Token refresh failed (HTTP ${status}).`);
  logToFile(`Token refresh failed (HTTP ${status}).`);
  return false;
}

async function getOffers() {
  const body = {
    apiVersion: "V2",
    filters: {
      serviceAreaFilter: SERVICE_AREA_IDS.length > 0 ? SERVICE_AREA_IDS : [],
      timeFilter: {
        startTime: new Date().toISOString(),
        endTime: isoFuture(48),
      },
    },
    serviceAreaIds: SERVICE_AREA_IDS,
  };

  return fetchWithTimeout(`${BASE_URL}/GetOffersForProviderPost`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Main polling loop
// ---------------------------------------------------------------------------

let running = true;
let consecutiveErrors = 0;

function sleep(ms) {
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, ms);
    // Allow graceful shutdown to break out of sleep
    const check = setInterval(() => {
      if (!running) {
        clearTimeout(timer);
        clearInterval(check);
        resolve();
      }
    }, 500);
  });
}

async function pollOnce() {
  const { status, data, error } = await getOffers();

  if (error) {
    console.error(`[${timestamp()}] Request error: ${error}`);
    logToFile(`Request error: ${error}`);
    consecutiveErrors++;
    return;
  }

  if (status === 200) {
    consecutiveErrors = 0;
    const offers = Array.isArray(data?.offerList) ? data.offerList : [];
    console.log(`[${timestamp()}] OK — ${offers.length} offer(s) found.`);

    if (offers.length > 0) {
      for (const offer of offers) {
        const start = offer.startTime || offer.expirationDate || "?";
        const location = offer.serviceAreaId || "?";
        const rate = offer.rateInfo?.priceAmount
          ? `$${(offer.rateInfo.priceAmount / 100).toFixed(2)}`
          : "?";
        const msg = `OFFER: location=${location} start=${start} rate=${rate}`;
        console.log(`  ${msg}`);
        logToFile(msg);
      }
    }
    return;
  }

  if (status === 401 || status === 403) {
    console.warn(
      `[${timestamp()}] HTTP ${status} — access token may be expired.`
    );
    logToFile(`HTTP ${status} — attempting token refresh.`);
    const refreshed = await refreshAccessToken();
    if (!refreshed) {
      console.error(
        `[${timestamp()}] Unable to refresh token. Set FLEX_REFRESH_TOKEN or update FLEX_ACCESS_TOKEN.`
      );
      consecutiveErrors++;
    }
    return;
  }

  if (status === 400 || status === 420) {
    consecutiveErrors++;
    const backoff = Math.min(
      consecutiveErrors * BACKOFF_STEP_MS,
      MAX_BACKOFF_MS
    );
    console.warn(
      `[${timestamp()}] HTTP ${status} — throttled. Backing off ${Math.round(backoff / 1000)}s (${consecutiveErrors} consecutive error(s)).`
    );
    logToFile(
      `HTTP ${status} — backing off ${Math.round(backoff / 1000)}s.`
    );
    await sleep(backoff);
    return;
  }

  // Other unexpected status
  consecutiveErrors++;
  console.warn(
    `[${timestamp()}] HTTP ${status}: ${JSON.stringify(data).slice(0, 200)}`
  );
  logToFile(`HTTP ${status}: ${JSON.stringify(data).slice(0, 200)}`);
}

async function main() {
  console.log("Amazon Flex Scraper starting...");
  console.log(`  Region:        ${REGION} (${BASE_URL})`);
  console.log(
    `  Token:         ${accessToken ? accessToken.slice(0, 12) + "..." : "(not set)"}`
  );
  console.log(
    `  Service areas: ${SERVICE_AREA_IDS.length > 0 ? SERVICE_AREA_IDS.join(", ") : "(none)"}`
  );
  console.log(
    `  Refresh token: ${REFRESH_TOKEN ? "configured" : "not set"}`
  );
  console.log();

  if (!accessToken) {
    console.error(
      "Error: FLEX_ACCESS_TOKEN is required. See README.md for setup instructions."
    );
    process.exit(1);
  }

  if (SERVICE_AREA_IDS.length === 0) {
    console.warn(
      "Warning: FLEX_SERVICE_AREA_IDS is not set. Offers may not be returned without service area filters."
    );
  }

  // Graceful shutdown
  for (const signal of ["SIGINT", "SIGTERM"]) {
    process.on(signal, () => {
      console.log(`\n[${timestamp()}] Received ${signal}, shutting down...`);
      logToFile(`Received ${signal}, shutting down.`);
      running = false;
    });
  }

  console.log(`[${timestamp()}] Polling started.\n`);
  logToFile("Scraper started.");

  while (running) {
    await pollOnce();
    if (!running) break;
    const interval = randomInterval();
    console.log(
      `[${timestamp()}] Next poll in ${Math.round(interval / 1000)}s...`
    );
    await sleep(interval);
  }

  console.log(`[${timestamp()}] Scraper stopped.`);
  logToFile("Scraper stopped.");
}

main().catch(console.error);
