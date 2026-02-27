/**
 * Amazon Flex API Service
 * Ported from the Node.js scraper
 */

import { REGIONS, DEFAULT_USER_AGENT, RATE_LIMIT } from '../constants/config';
import { getTokens, getRegion, getServiceAreaIds } from '../utils/storage';

/**
 * Generate Amazon-formatted date
 */
function amzDate() {
  return new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
}

/**
 * Generate ISO date for future time
 */
function isoFuture(hoursFromNow) {
  const d = new Date();
  d.setHours(d.getHours() + hoursFromNow);
  return d.toISOString();
}

/**
 * Build request headers
 */
async function buildHeaders() {
  const { accessToken } = await getTokens();
  return {
    Accept: 'application/json',
    'Content-Type': 'application/json',
    'x-amz-access-token': accessToken,
    'X-Amz-Date': amzDate(),
    'User-Agent': DEFAULT_USER_AGENT,
  };
}

/**
 * Get base URL for current region
 */
async function getBaseUrl() {
  const region = await getRegion();
  return REGIONS[region]?.baseUrl || REGIONS.na.baseUrl;
}

/**
 * Make API request with timeout
 */
async function request(method, url, body = null) {
  const headers = await buildHeaders();
  const opts = {
    method,
    headers,
  };

  if (body) {
    opts.body = JSON.stringify(body);
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

    return { status: res.status, data, error: null };
  } catch (err) {
    clearTimeout(timeout);
    return { status: -1, data: null, error: err.message };
  }
}

/**
 * Get available delivery offers
 */
export async function getOffers() {
  const serviceAreaIds = await getServiceAreaIds();
  const baseUrl = await getBaseUrl();

  const body = {
    apiVersion: 'V2',
    filters: {
      serviceAreaFilter: serviceAreaIds,
      timeFilter: {
        startTime: new Date().toISOString(),
        endTime: isoFuture(48),
      },
    },
    serviceAreaIds,
  };

  return request('POST', `${baseUrl}/GetOffersForProviderPost`, body);
}

/**
 * Get service areas for the user
 */
export async function getServiceAreas() {
  const baseUrl = await getBaseUrl();
  return request('GET', `${baseUrl}/eligibleServiceAreas`);
}

/**
 * Accept an offer
 */
export async function acceptOffer(offerId) {
  const baseUrl = await getBaseUrl();

  const body = {
    offerId,
    apiVersion: 'V2',
  };

  return request('POST', `${baseUrl}/AcceptOffer`, body);
}

/**
 * Validate token by making a test request
 */
export async function validateToken() {
  const { accessToken } = await getTokens();
  if (!accessToken) {
    return { valid: false, error: 'No token found' };
  }

  const result = await getServiceAreas();

  if (result.status === 200) {
    return { valid: true, data: result.data };
  } else if (result.status === 401 || result.status === 403) {
    return { valid: false, error: 'Token expired or invalid' };
  } else {
    return { valid: false, error: result.error || `HTTP ${result.status}` };
  }
}

/**
 * Calculate delay for rate limiting
 */
export function calculateDelay(consecutiveErrors, currentBackoff) {
  if (consecutiveErrors > 0) {
    return currentBackoff;
  }

  const base =
    Math.random() * (RATE_LIMIT.MAX_INTERVAL_MS - RATE_LIMIT.MIN_INTERVAL_MS) +
    RATE_LIMIT.MIN_INTERVAL_MS;
  const jitter = (Math.random() - 0.5) * 2 * RATE_LIMIT.JITTER_MS;
  return Math.max(1000, Math.floor(base + jitter));
}

/**
 * Calculate backoff on error
 */
export function calculateBackoff(consecutiveErrors) {
  return Math.min(
    RATE_LIMIT.BACKOFF_ON_ERROR_MS * consecutiveErrors,
    RATE_LIMIT.MAX_BACKOFF_MS
  );
}
