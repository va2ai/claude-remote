/**
 * Secure Storage Utilities
 * Wrapper around expo-secure-store for token management
 */

import * as SecureStore from 'expo-secure-store';
import { STORAGE_KEYS } from '../constants/config';

/**
 * Save authentication tokens
 */
export async function saveTokens(accessToken, refreshToken = null) {
  await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
  if (refreshToken) {
    await SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
  }
}

/**
 * Get authentication tokens
 */
export async function getTokens() {
  const accessToken = await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
  const refreshToken = await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
  return { accessToken, refreshToken };
}

/**
 * Clear all authentication tokens
 */
export async function clearTokens() {
  await SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
  await SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated() {
  const { accessToken } = await getTokens();
  return !!accessToken;
}

/**
 * Save region preference
 */
export async function saveRegion(region) {
  await SecureStore.setItemAsync(STORAGE_KEYS.REGION, region);
}

/**
 * Get region preference
 */
export async function getRegion() {
  return (await SecureStore.getItemAsync(STORAGE_KEYS.REGION)) || 'na';
}

/**
 * Save service area IDs
 */
export async function saveServiceAreaIds(ids) {
  await SecureStore.setItemAsync(STORAGE_KEYS.SERVICE_AREA_IDS, JSON.stringify(ids));
}

/**
 * Get service area IDs
 */
export async function getServiceAreaIds() {
  const data = await SecureStore.getItemAsync(STORAGE_KEYS.SERVICE_AREA_IDS);
  return data ? JSON.parse(data) : [];
}

/**
 * Save poll interval
 */
export async function savePollInterval(intervalMs) {
  await SecureStore.setItemAsync(STORAGE_KEYS.POLL_INTERVAL, String(intervalMs));
}

/**
 * Get poll interval
 */
export async function getPollInterval() {
  const data = await SecureStore.getItemAsync(STORAGE_KEYS.POLL_INTERVAL);
  return data ? parseInt(data, 10) : 30000;
}
