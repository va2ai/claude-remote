/**
 * Authentication Hook
 * Manages token state and validation
 */

import { useState, useEffect, useCallback } from 'react';
import {
  getTokens,
  saveTokens,
  clearTokens,
  isAuthenticated,
  saveRegion,
  getRegion,
} from '../utils/storage';
import { validateToken } from '../services/flexApi';
import { DEFAULT_TOKENS } from '../constants/defaultTokens';

export function useAuth() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [region, setRegionState] = useState('na');
  const [tokenStatus, setTokenStatus] = useState(null);

  // Check authentication status on mount
  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = useCallback(async () => {
    setLoading(true);
    try {
      let isAuth = await isAuthenticated();

      // Auto-load default tokens if none stored
      if (!isAuth && DEFAULT_TOKENS.access_token) {
        console.log('No stored tokens found, loading default tokens...');
        await saveTokens(DEFAULT_TOKENS.access_token, DEFAULT_TOKENS.refresh_token);
        isAuth = true;
      }

      setAuthenticated(isAuth);

      const savedRegion = await getRegion();
      setRegionState(savedRegion);

      if (isAuth) {
        // Validate token
        const result = await validateToken();
        setTokenStatus(result.valid ? 'valid' : 'invalid');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setAuthenticated(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (accessToken, refreshToken = null) => {
    try {
      await saveTokens(accessToken, refreshToken);
      setAuthenticated(true);

      // Validate immediately
      const result = await validateToken();
      setTokenStatus(result.valid ? 'valid' : 'invalid');

      return result;
    } catch (error) {
      console.error('Login failed:', error);
      return { valid: false, error: error.message };
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await clearTokens();
      setAuthenticated(false);
      setTokenStatus(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, []);

  const setRegion = useCallback(async (newRegion) => {
    await saveRegion(newRegion);
    setRegionState(newRegion);
  }, []);

  const refreshAuth = useCallback(async () => {
    const result = await validateToken();
    setTokenStatus(result.valid ? 'valid' : 'invalid');
    if (!result.valid) {
      setAuthenticated(false);
    }
    return result;
  }, []);

  return {
    authenticated,
    loading,
    region,
    tokenStatus,
    login,
    logout,
    setRegion,
    refreshAuth,
    checkAuth,
  };
}
