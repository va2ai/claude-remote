/**
 * Flex Monitor Configuration
 */

export const REGIONS = {
  na: {
    name: 'North America',
    baseUrl: 'https://flex-capacity-na.amazon.com',
  },
  eu: {
    name: 'Europe',
    baseUrl: 'https://flex-capacity-eu.amazon.com',
  },
  fe: {
    name: 'Far East',
    baseUrl: 'https://flex-capacity-fe.amazon.com',
  },
};

export const DEFAULT_USER_AGENT =
  'iOS/16.1 (iPhone Darwin) Model/iPhone FlexApp/3.96.2.61.0';

export const RATE_LIMIT = {
  MIN_INTERVAL_MS: 30000,
  MAX_INTERVAL_MS: 60000,
  BACKOFF_ON_ERROR_MS: 300000,
  MAX_BACKOFF_MS: 1800000,
  JITTER_MS: 5000,
};

// Background fetch interval (iOS minimum is 15 minutes)
export const BACKGROUND_FETCH_INTERVAL = 15 * 60;

// Storage keys
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'flex_access_token',
  REFRESH_TOKEN: 'flex_refresh_token',
  REGION: 'flex_region',
  SERVICE_AREA_IDS: 'flex_service_area_ids',
  POLL_INTERVAL: 'flex_poll_interval',
};
