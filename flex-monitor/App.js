/**
 * Flex Monitor - Amazon Flex Offer Monitor
 * Main application entry point with navigation
 */

import React, { useState, useEffect, useCallback } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import * as Notifications from 'expo-notifications';
import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';

import LoginScreen from './src/screens/LoginScreen';
import DashboardScreen from './src/screens/DashboardScreen';
import SettingsScreen from './src/screens/SettingsScreen';
import { useAuth } from './src/hooks/useAuth';
import { getOffers } from './src/services/flexApi';
import { getServiceAreaIds } from './src/utils/storage';
import { BACKGROUND_FETCH_INTERVAL } from './src/constants/config';

const Stack = createNativeStackNavigator();

const BACKGROUND_FETCH_TASK = 'background-flex-fetch';

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

// Define background fetch task
TaskManager.defineTask(BACKGROUND_FETCH_TASK, async () => {
  try {
    const serviceAreaIds = await getServiceAreaIds();
    if (serviceAreaIds.length === 0) {
      return BackgroundFetch.BackgroundFetchResult.NoData;
    }

    const result = await getOffers();

    if (result.status === 200) {
      const offers = result.data?.offerList || [];
      if (offers.length > 0) {
        // Send notification
        const offer = offers[0];
        const startTime = new Date(offer.startTime).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        });
        const payment = offer.payment?.amount
          ? `$${offer.payment.amount}`
          : 'Unknown pay';

        await Notifications.scheduleNotificationAsync({
          content: {
            title: `${offers.length} Flex Block${offers.length > 1 ? 's' : ''} Available!`,
            body: `${startTime} - ${payment}`,
            sound: true,
          },
          trigger: null,
        });

        return BackgroundFetch.BackgroundFetchResult.NewData;
      }
    }

    return BackgroundFetch.BackgroundFetchResult.NoData;
  } catch (error) {
    console.error('Background fetch failed:', error);
    return BackgroundFetch.BackgroundFetchResult.Failed;
  }
});

// Register background fetch
async function registerBackgroundFetch() {
  try {
    await BackgroundFetch.registerTaskAsync(BACKGROUND_FETCH_TASK, {
      minimumInterval: BACKGROUND_FETCH_INTERVAL,
      stopOnTerminate: false,
      startOnBoot: true,
    });
    console.log('Background fetch registered');
  } catch (error) {
    console.error('Background fetch registration failed:', error);
  }
}

export default function App() {
  const {
    authenticated,
    loading,
    region,
    login,
    logout,
    setRegion,
  } = useAuth();

  useEffect(() => {
    // Register background fetch when authenticated
    if (authenticated) {
      registerBackgroundFetch();
    }
  }, [authenticated]);

  const handleLogin = useCallback(
    async (accessToken, refreshToken, selectedRegion) => {
      await setRegion(selectedRegion);
      return await login(accessToken, refreshToken);
    },
    [login, setRegion]
  );

  if (loading) {
    return null; // Or a loading screen
  }

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: '#1a1a2e',
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          contentStyle: {
            backgroundColor: '#1a1a2e',
          },
        }}
      >
        {!authenticated ? (
          <Stack.Screen name="Login" options={{ headerShown: false }}>
            {(props) => (
              <LoginScreen
                {...props}
                onLogin={handleLogin}
                initialRegion={region}
              />
            )}
          </Stack.Screen>
        ) : (
          <>
            <Stack.Screen
              name="Dashboard"
              component={DashboardScreen}
              options={{ headerShown: false }}
            />
            <Stack.Screen name="Settings">
              {(props) => <SettingsScreen {...props} onLogout={logout} />}
            </Stack.Screen>
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
