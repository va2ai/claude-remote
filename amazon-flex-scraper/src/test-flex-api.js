#!/usr/bin/env node

/**
 * Amazon Flex API Test Script
 *
 * Tests connectivity and responses from the reverse-engineered Amazon Flex API endpoints.
 * Requires a valid access token (and optionally a refresh token) set via environment
 * variables or a .env file in the project root.
 *
 * Usage:
 *   node src/test-flex-api.js                  # run all tests
 *   node src/test-flex-api.js --test auth      # run only auth tests
 *   node src/test-flex-api.js --test offers    # run only offers tests
 *   node src/test-flex-api.js --test areas     # run only service-areas tests
 *   node src/test-flex-api.js --test filters   # run only filters tests
 *   node src/test-flex-api.js --dry-run        # print requests without sending
 */

const { readFileSync, existsSync } = require("fs");
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

// ---------------------------------------------------------------------------
// Helpers
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

const ACCESS_TOKEN = env("FLEX_ACCESS_TOKEN");
const REFRESH_TOKEN = env("FLEX_REFRESH_TOKEN");
const REGION = env("FLEX_REGION", "na");
const SERVICE_AREA_IDS = env("FLEX_SERVICE_AREA_IDS", "")
  .split(",")
  .map((s) => s.trim())
  .filter(Boolean);

const BASE_URL = REGIONS[REGION] || REGIONS.na;

function amzDate() {
  return new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
}

function headers(token) {
  return {
    Accept: "application/json",
    "Content-Type": "application/json",
    "x-amz-access-token": token || ACCESS_TOKEN,
    "X-Amz-Date": amzDate(),
    "User-Agent": DEFAULT_USER_AGENT,
  };
}

function isoFuture(hoursFromNow) {
  const d = new Date();
  d.setHours(d.getHours() + hoursFromNow);
  return d.toISOString();
}

const PASS = "\x1b[32mPASS\x1b[0m";
const FAIL = "\x1b[31mFAIL\x1b[0m";
const SKIP = "\x1b[33mSKIP\x1b[0m";
const BOLD = "\x1b[1m";
const RESET = "\x1b[0m";

const results = { pass: 0, fail: 0, skip: 0 };

function log(status, name, detail) {
  const tag = status === "pass" ? PASS : status === "fail" ? FAIL : SKIP;
  console.log(`  ${tag}  ${name}${detail ? " — " + detail : ""}`);
  results[status]++;
}

async function request(method, url, body, customHeaders) {
  const opts = {
    method,
    headers: customHeaders || headers(),
  };
  if (body) opts.body = JSON.stringify(body);

  const args = parseArgs();
  if (args.dryRun) {
    console.log(`    [dry-run] ${method} ${url}`);
    if (body) console.log(`    body: ${JSON.stringify(body, null, 2)}`);
    return { status: 0, data: null, dryRun: true };
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
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

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = { testFilter: null, dryRun: false };
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--test" && args[i + 1]) {
      parsed.testFilter = args[++i];
    }
    if (args[i] === "--dry-run") {
      parsed.dryRun = true;
    }
  }
  return parsed;
}

// ---------------------------------------------------------------------------
// Test suites
// ---------------------------------------------------------------------------

async function testAuth() {
  console.log(`\n${BOLD}Auth / Token Tests${RESET}`);

  // 1. Verify access token is configured
  if (!ACCESS_TOKEN) {
    log("skip", "Access token present", "FLEX_ACCESS_TOKEN not set");
    log("skip", "Token refresh", "no tokens available");
    return;
  }
  log("pass", "Access token present", `${ACCESS_TOKEN.slice(0, 12)}...`);

  // 2. Test token refresh (if refresh token available)
  if (!REFRESH_TOKEN) {
    log("skip", "Token refresh", "FLEX_REFRESH_TOKEN not set");
    return;
  }

  const { status, data, dryRun } = await request(
    "POST",
    `${AUTH_BASE}/auth/token`,
    {
      source_token_type: "refresh_token",
      source_token: REFRESH_TOKEN,
      requested_token_type: "access_token",
    },
    {
      "Content-Type": "application/json",
      Accept: "application/json",
    }
  );

  if (dryRun) {
    log("skip", "Token refresh", "dry-run mode");
    return;
  }

  if (status === 200 && data && data.access_token) {
    log("pass", "Token refresh", "received new access token");
  } else {
    log("fail", "Token refresh", `HTTP ${status}: ${JSON.stringify(data)}`);
  }
}

async function testGetOffers() {
  console.log(`\n${BOLD}Get Offers Tests${RESET}`);

  if (!ACCESS_TOKEN) {
    log("skip", "Get offers", "FLEX_ACCESS_TOKEN not set");
    return;
  }

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

  const { status, data, dryRun, error } = await request(
    "POST",
    `${BASE_URL}/GetOffersForProviderPost`,
    body
  );

  if (dryRun) {
    log("skip", "Get offers", "dry-run mode");
    return;
  }

  if (error) {
    log("fail", "Get offers — connectivity", error);
    return;
  }

  // Any HTTP response means the endpoint is reachable
  if (status >= 200 && status < 500) {
    log("pass", "Get offers — endpoint reachable", `HTTP ${status}`);
  } else {
    log("fail", "Get offers — endpoint reachable", `HTTP ${status}`);
  }

  // Check for a valid 200 with offer data
  if (status === 200) {
    const offerCount = Array.isArray(data?.offerList)
      ? data.offerList.length
      : "unknown";
    log("pass", "Get offers — response OK", `${offerCount} offer(s) returned`);
  } else if (status === 400) {
    log(
      "fail",
      "Get offers — response",
      "400 — possible CAPTCHA / throttle (30-min cooldown)"
    );
  } else if (status === 401 || status === 403) {
    log(
      "fail",
      "Get offers — auth",
      `${status} — access token may be expired`
    );
  } else {
    log("fail", "Get offers — response", `HTTP ${status}: ${JSON.stringify(data)}`);
  }
}

async function testServiceAreas() {
  console.log(`\n${BOLD}Service Areas Tests${RESET}`);

  if (!ACCESS_TOKEN) {
    log("skip", "Eligible service areas", "FLEX_ACCESS_TOKEN not set");
    return;
  }

  const { status, data, dryRun, error } = await request(
    "GET",
    `${BASE_URL}/eligibleServiceAreas`
  );

  if (dryRun) {
    log("skip", "Eligible service areas", "dry-run mode");
    return;
  }

  if (error) {
    log("fail", "Eligible service areas — connectivity", error);
    return;
  }

  if (status >= 200 && status < 500) {
    log("pass", "Eligible service areas — endpoint reachable", `HTTP ${status}`);
  } else {
    log("fail", "Eligible service areas — endpoint reachable", `HTTP ${status}`);
  }

  if (status === 200 && data) {
    const areaCount = Array.isArray(data) ? data.length : Object.keys(data).length;
    log(
      "pass",
      "Eligible service areas — response OK",
      `${areaCount} area(s) returned`
    );
  } else if (status === 401 || status === 403) {
    log(
      "fail",
      "Eligible service areas — auth",
      `${status} — access token may be expired`
    );
  }
}

async function testOfferFilters() {
  console.log(`\n${BOLD}Offer Filters Tests${RESET}`);

  if (!ACCESS_TOKEN) {
    log("skip", "Offer filter options", "FLEX_ACCESS_TOKEN not set");
    return;
  }

  const { status, data, dryRun, error } = await request(
    "GET",
    `${BASE_URL}/getOfferFiltersOptions`
  );

  if (dryRun) {
    log("skip", "Offer filter options", "dry-run mode");
    return;
  }

  if (error) {
    log("fail", "Offer filter options — connectivity", error);
    return;
  }

  if (status >= 200 && status < 500) {
    log("pass", "Offer filter options — endpoint reachable", `HTTP ${status}`);
  } else {
    log("fail", "Offer filter options — endpoint reachable", `HTTP ${status}`);
  }

  if (status === 200 && data) {
    log("pass", "Offer filter options — response OK", JSON.stringify(data).slice(0, 80));
  } else if (status === 401 || status === 403) {
    log(
      "fail",
      "Offer filter options — auth",
      `${status} — access token may be expired`
    );
  }
}

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------

const SUITES = {
  auth: testAuth,
  offers: testGetOffers,
  areas: testServiceAreas,
  filters: testOfferFilters,
};

async function run() {
  const args = parseArgs();

  console.log(`${BOLD}Amazon Flex API Test Suite${RESET}`);
  console.log(`Region:  ${REGION} (${BASE_URL})`);
  console.log(`Token:   ${ACCESS_TOKEN ? ACCESS_TOKEN.slice(0, 12) + "..." : "(not set)"}`);
  if (args.dryRun) console.log(`Mode:    dry-run`);
  if (args.testFilter) console.log(`Filter:  ${args.testFilter}`);

  const suitesToRun = args.testFilter
    ? { [args.testFilter]: SUITES[args.testFilter] }
    : SUITES;

  if (args.testFilter && !SUITES[args.testFilter]) {
    console.error(
      `\nUnknown test suite: "${args.testFilter}". Available: ${Object.keys(SUITES).join(", ")}`
    );
    process.exit(1);
  }

  for (const suite of Object.values(suitesToRun)) {
    await suite();
  }

  console.log(`\n${BOLD}Results${RESET}`);
  console.log(
    `  ${results.pass} passed, ${results.fail} failed, ${results.skip} skipped`
  );

  if (results.fail > 0) process.exit(1);
}

run().catch((err) => {
  console.error("Unexpected error:", err);
  process.exit(1);
});
