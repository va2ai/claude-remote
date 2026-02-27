/**
 * Offers Polling Hook
 * Manages offer fetching and polling state
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { AppState } from 'react-native';
import { getOffers, calculateDelay, calculateBackoff } from '../services/flexApi';
import { getServiceAreaIds, getPollInterval } from '../utils/storage';

export function useOffers() {
  const [offers, setOffers] = useState([]);
  const [lastChecked, setLastChecked] = useState(null);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalChecks: 0,
    offersFound: 0,
    errors: 0,
    consecutiveErrors: 0,
  });

  const pollingRef = useRef(false);
  const timeoutRef = useRef(null);
  const consecutiveErrorsRef = useRef(0);
  const currentBackoffRef = useRef(30000);

  // Clear polling on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Handle app state changes
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState) => {
      if (nextAppState === 'active' && pollingRef.current) {
        // App came to foreground, poll immediately
        pollOnce();
      }
    });

    return () => {
      subscription.remove();
    };
  }, []);

  const pollOnce = useCallback(async () => {
    const serviceAreaIds = await getServiceAreaIds();

    if (serviceAreaIds.length === 0) {
      setError('No service areas configured');
      return { success: false, offers: [], error: 'No service areas configured' };
    }

    setError(null);

    try {
      const result = await getOffers();
      setLastChecked(new Date());

      setStats((prev) => ({
        ...prev,
        totalChecks: prev.totalChecks + 1,
      }));

      if (result.status === 200) {
        consecutiveErrorsRef.current = 0;
        currentBackoffRef.current = 30000;

        const offerList = result.data?.offerList || [];
        setOffers(offerList);

        if (offerList.length > 0) {
          setStats((prev) => ({
            ...prev,
            offersFound: prev.offersFound + offerList.length,
            consecutiveErrors: 0,
          }));
        }

        return { success: true, offers: offerList, error: null };
      } else if (result.status === 400 || result.status === 420) {
        consecutiveErrorsRef.current++;
        currentBackoffRef.current = calculateBackoff(consecutiveErrorsRef.current);

        const errMsg = `Rate limited (HTTP ${result.status})`;
        setError(errMsg);
        setStats((prev) => ({
          ...prev,
          errors: prev.errors + 1,
          consecutiveErrors: consecutiveErrorsRef.current,
        }));

        return { success: false, offers: [], error: errMsg };
      } else if (result.status === 401 || result.status === 403) {
        const errMsg = 'Token expired';
        setError(errMsg);
        consecutiveErrorsRef.current++;
        setStats((prev) => ({
          ...prev,
          errors: prev.errors + 1,
          consecutiveErrors: consecutiveErrorsRef.current,
        }));

        return { success: false, offers: [], error: errMsg };
      } else {
        consecutiveErrorsRef.current++;
        const errMsg = result.error || `HTTP ${result.status}`;
        setError(errMsg);
        setStats((prev) => ({
          ...prev,
          errors: prev.errors + 1,
          consecutiveErrors: consecutiveErrorsRef.current,
        }));

        return { success: false, offers: [], error: errMsg };
      }
    } catch (err) {
      consecutiveErrorsRef.current++;
      const errMsg = err.message;
      setError(errMsg);
      setStats((prev) => ({
        ...prev,
        errors: prev.errors + 1,
        consecutiveErrors: consecutiveErrorsRef.current,
      }));

      return { success: false, offers: [], error: errMsg };
    }
  }, []);

  const startPolling = useCallback(async () => {
    if (pollingRef.current) return;

    pollingRef.current = true;
    setPolling(true);
    setError(null);

    const poll = async () => {
      if (!pollingRef.current) return;

      await pollOnce();

      if (pollingRef.current) {
        const delay = calculateDelay(
          consecutiveErrorsRef.current,
          currentBackoffRef.current
        );
        timeoutRef.current = setTimeout(poll, delay);
      }
    };

    // Start polling immediately
    poll();
  }, [pollOnce]);

  const stopPolling = useCallback(() => {
    pollingRef.current = false;
    setPolling(false);

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  const resetStats = useCallback(() => {
    setStats({
      totalChecks: 0,
      offersFound: 0,
      errors: 0,
      consecutiveErrors: 0,
    });
    consecutiveErrorsRef.current = 0;
    currentBackoffRef.current = 30000;
  }, []);

  return {
    offers,
    lastChecked,
    polling,
    error,
    stats,
    pollOnce,
    startPolling,
    stopPolling,
    resetStats,
  };
}
