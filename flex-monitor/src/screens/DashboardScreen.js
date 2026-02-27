/**
 * Dashboard Screen
 * Main monitoring interface with offer display
 */

import React, { useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  RefreshControl,
} from 'react-native';
import * as Notifications from 'expo-notifications';
import { useOffers } from '../hooks/useOffers';

export default function DashboardScreen({ navigation }) {
  const {
    offers,
    lastChecked,
    polling,
    error,
    stats,
    pollOnce,
    startPolling,
    stopPolling,
  } = useOffers();

  // Send notification when offers found
  useEffect(() => {
    if (offers.length > 0 && polling) {
      sendNotification(offers);
    }
  }, [offers]);

  const sendNotification = async (newOffers) => {
    const { status } = await Notifications.getPermissionsAsync();
    if (status !== 'granted') return;

    const offer = newOffers[0];
    const startTime = new Date(offer.startTime).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
    const payment = offer.payment?.amount
      ? `$${offer.payment.amount}`
      : 'Unknown pay';

    await Notifications.scheduleNotificationAsync({
      content: {
        title: `${newOffers.length} Flex Block${newOffers.length > 1 ? 's' : ''} Available!`,
        body: `${startTime} - ${payment}`,
        sound: true,
      },
      trigger: null,
    });
  };

  const formatTime = (date) => {
    if (!date) return 'Never';
    return date.toLocaleTimeString();
  };

  const formatOfferTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleString([], {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <View style={styles.container}>
      {/* Status Bar */}
      <View style={styles.statusBar}>
        <View style={styles.statusItem}>
          <View
            style={[
              styles.statusDot,
              polling ? styles.statusDotActive : styles.statusDotInactive,
            ]}
          />
          <Text style={styles.statusText}>
            {polling ? 'Monitoring' : 'Stopped'}
          </Text>
        </View>
        <Text style={styles.statusTime}>
          Last check: {formatTime(lastChecked)}
        </Text>
      </View>

      {/* Error Display */}
      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Stats */}
      <View style={styles.statsContainer}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats.totalChecks}</Text>
          <Text style={styles.statLabel}>Checks</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats.offersFound}</Text>
          <Text style={styles.statLabel}>Found</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{stats.errors}</Text>
          <Text style={styles.statLabel}>Errors</Text>
        </View>
      </View>

      {/* Control Buttons */}
      <View style={styles.controlsContainer}>
        {polling ? (
          <TouchableOpacity
            style={[styles.controlButton, styles.stopButton]}
            onPress={stopPolling}
          >
            <Text style={styles.controlButtonText}>Stop Monitoring</Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.controlButton, styles.startButton]}
            onPress={startPolling}
          >
            <Text style={styles.controlButtonText}>Start Monitoring</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity
          style={[styles.controlButton, styles.checkButton]}
          onPress={pollOnce}
        >
          <Text style={styles.controlButtonText}>Check Now</Text>
        </TouchableOpacity>
      </View>

      {/* Offers List */}
      <View style={styles.offersContainer}>
        <Text style={styles.offersTitle}>
          Available Offers ({offers.length})
        </Text>
        <ScrollView
          style={styles.offersList}
          refreshControl={
            <RefreshControl
              refreshing={false}
              onRefresh={pollOnce}
              tintColor="#ff6b35"
            />
          }
        >
          {offers.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyStateText}>
                No offers available right now
              </Text>
              <Text style={styles.emptyStateSubtext}>
                Pull down to refresh or start monitoring
              </Text>
            </View>
          ) : (
            offers.map((offer, index) => (
              <View key={offer.offerId || index} style={styles.offerCard}>
                <View style={styles.offerHeader}>
                  <Text style={styles.offerPayment}>
                    ${offer.payment?.amount || '?'}
                  </Text>
                  <Text style={styles.offerDuration}>
                    {offer.duration
                      ? `${Math.round(offer.duration / 60)} hrs`
                      : ''}
                  </Text>
                </View>
                <Text style={styles.offerTime}>
                  {formatOfferTime(offer.startTime)}
                </Text>
                <Text style={styles.offerLocation}>
                  {offer.serviceAreaId || 'Unknown location'}
                </Text>
              </View>
            ))
          )}
        </ScrollView>
      </View>

      {/* Settings Button */}
      <TouchableOpacity
        style={styles.settingsButton}
        onPress={() => navigation.navigate('Settings')}
      >
        <Text style={styles.settingsButtonText}>Settings</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    padding: 20,
    paddingTop: 60,
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  statusItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 8,
  },
  statusDotActive: {
    backgroundColor: '#4ade80',
  },
  statusDotInactive: {
    backgroundColor: '#666',
  },
  statusText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  statusTime: {
    color: '#888',
    fontSize: 12,
  },
  errorContainer: {
    backgroundColor: '#ff4444',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#fff',
    textAlign: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#2a2a4a',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
  },
  statLabel: {
    color: '#888',
    fontSize: 12,
    marginTop: 4,
  },
  controlsContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  controlButton: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  startButton: {
    backgroundColor: '#4ade80',
  },
  stopButton: {
    backgroundColor: '#ff4444',
  },
  checkButton: {
    backgroundColor: '#3b82f6',
  },
  controlButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  offersContainer: {
    flex: 1,
    backgroundColor: '#2a2a4a',
    borderRadius: 12,
    padding: 16,
  },
  offersTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  offersList: {
    flex: 1,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    color: '#888',
    fontSize: 16,
  },
  emptyStateSubtext: {
    color: '#666',
    fontSize: 12,
    marginTop: 8,
  },
  offerCard: {
    backgroundColor: '#1a1a2e',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
  },
  offerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  offerPayment: {
    color: '#4ade80',
    fontSize: 24,
    fontWeight: 'bold',
  },
  offerDuration: {
    color: '#888',
    fontSize: 14,
  },
  offerTime: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 4,
  },
  offerLocation: {
    color: '#888',
    fontSize: 12,
  },
  settingsButton: {
    marginTop: 12,
    padding: 12,
    alignItems: 'center',
  },
  settingsButtonText: {
    color: '#ff6b35',
    fontSize: 16,
  },
});
