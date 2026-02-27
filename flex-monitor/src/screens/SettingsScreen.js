/**
 * Settings Screen
 * Configure region, service areas, and polling intervals
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  Switch,
} from 'react-native';
import * as Notifications from 'expo-notifications';
import { REGIONS } from '../constants/config';
import {
  getRegion,
  saveRegion,
  getServiceAreaIds,
  saveServiceAreaIds,
  getPollInterval,
  savePollInterval,
} from '../utils/storage';
import { getServiceAreas } from '../services/flexApi';

export default function SettingsScreen({ navigation, onLogout }) {
  const [region, setRegion] = useState('na');
  const [serviceAreaIds, setServiceAreaIds] = useState('');
  const [availableAreas, setAvailableAreas] = useState([]);
  const [pollInterval, setPollInterval] = useState('30');
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
    checkNotificationPermissions();
  }, []);

  const loadSettings = async () => {
    try {
      const savedRegion = await getRegion();
      const savedAreas = await getServiceAreaIds();
      const savedInterval = await getPollInterval();

      setRegion(savedRegion);
      setServiceAreaIds(savedAreas.join(', '));
      setPollInterval(String(savedInterval / 1000));

      // Load available service areas
      await loadServiceAreas();
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadServiceAreas = async () => {
    try {
      const result = await getServiceAreas();
      if (result.status === 200 && result.data?.serviceAreaIds) {
        setAvailableAreas(result.data.serviceAreaIds);
      }
    } catch (error) {
      console.error('Failed to load service areas:', error);
    }
  };

  const checkNotificationPermissions = async () => {
    const { status } = await Notifications.getPermissionsAsync();
    setNotificationsEnabled(status === 'granted');
  };

  const requestNotificationPermissions = async () => {
    const { status } = await Notifications.requestPermissionsAsync();
    setNotificationsEnabled(status === 'granted');
    if (status !== 'granted') {
      Alert.alert(
        'Permissions Required',
        'Please enable notifications in your device settings to receive alerts when offers are found.'
      );
    }
  };

  const handleSave = async () => {
    try {
      await saveRegion(region);

      const areas = serviceAreaIds
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      await saveServiceAreaIds(areas);

      const intervalMs = parseInt(pollInterval, 10) * 1000;
      if (intervalMs >= 10000) {
        await savePollInterval(intervalMs);
      }

      Alert.alert('Saved', 'Settings have been updated');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings');
    }
  };

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to logout?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Logout',
        style: 'destructive',
        onPress: onLogout,
      },
    ]);
  };

  const toggleServiceArea = (areaId) => {
    const currentAreas = serviceAreaIds
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);

    if (currentAreas.includes(areaId)) {
      const newAreas = currentAreas.filter((id) => id !== areaId);
      setServiceAreaIds(newAreas.join(', '));
    } else {
      setServiceAreaIds([...currentAreas, areaId].join(', '));
    }
  };

  const selectedAreas = serviceAreaIds
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Region</Text>
        <View style={styles.regionContainer}>
          {Object.entries(REGIONS).map(([key, { name }]) => (
            <TouchableOpacity
              key={key}
              style={[
                styles.regionButton,
                region === key && styles.regionButtonActive,
              ]}
              onPress={() => setRegion(key)}
            >
              <Text
                style={[
                  styles.regionButtonText,
                  region === key && styles.regionButtonTextActive,
                ]}
              >
                {name}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Service Areas</Text>
        {availableAreas.length > 0 ? (
          <View style={styles.areasContainer}>
            {availableAreas.map((area) => (
              <TouchableOpacity
                key={area}
                style={[
                  styles.areaChip,
                  selectedAreas.includes(area) && styles.areaChipSelected,
                ]}
                onPress={() => toggleServiceArea(area)}
              >
                <Text
                  style={[
                    styles.areaChipText,
                    selectedAreas.includes(area) && styles.areaChipTextSelected,
                  ]}
                >
                  {area}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : (
          <>
            <Text style={styles.hint}>
              Enter service area IDs (comma separated)
            </Text>
            <TextInput
              style={styles.input}
              value={serviceAreaIds}
              onChangeText={setServiceAreaIds}
              placeholder="e.g., 1234abcd, 5678efgh"
              placeholderTextColor="#666"
              autoCapitalize="none"
            />
          </>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Poll Interval</Text>
        <View style={styles.intervalContainer}>
          <TextInput
            style={styles.intervalInput}
            value={pollInterval}
            onChangeText={setPollInterval}
            keyboardType="numeric"
            placeholder="30"
            placeholderTextColor="#666"
          />
          <Text style={styles.intervalLabel}>seconds</Text>
        </View>
        <Text style={styles.hint}>Minimum: 10 seconds (30+ recommended)</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifications</Text>
        <View style={styles.switchRow}>
          <Text style={styles.switchLabel}>Push Notifications</Text>
          <Switch
            value={notificationsEnabled}
            onValueChange={(value) => {
              if (value) {
                requestNotificationPermissions();
              }
            }}
            trackColor={{ false: '#444', true: '#ff6b35' }}
            thumbColor={notificationsEnabled ? '#fff' : '#888'}
          />
        </View>
        <Text style={styles.hint}>
          Get notified when new offers are available
        </Text>
      </View>

      <TouchableOpacity style={styles.saveButton} onPress={handleSave}>
        <Text style={styles.saveButtonText}>Save Settings</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutButtonText}>Logout</Text>
      </TouchableOpacity>

      <View style={styles.spacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
    padding: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  regionContainer: {
    flexDirection: 'row',
    gap: 10,
  },
  regionButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#2a2a4a',
    alignItems: 'center',
  },
  regionButtonActive: {
    backgroundColor: '#ff6b35',
  },
  regionButtonText: {
    color: '#aaa',
    fontWeight: '600',
  },
  regionButtonTextActive: {
    color: '#fff',
  },
  input: {
    backgroundColor: '#2a2a4a',
    borderRadius: 8,
    padding: 16,
    color: '#fff',
    fontSize: 16,
  },
  hint: {
    color: '#666',
    fontSize: 12,
    marginTop: 8,
  },
  areasContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  areaChip: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    backgroundColor: '#2a2a4a',
  },
  areaChipSelected: {
    backgroundColor: '#ff6b35',
  },
  areaChipText: {
    color: '#aaa',
    fontSize: 14,
  },
  areaChipTextSelected: {
    color: '#fff',
  },
  intervalContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  intervalInput: {
    backgroundColor: '#2a2a4a',
    borderRadius: 8,
    padding: 16,
    color: '#fff',
    fontSize: 16,
    width: 100,
    textAlign: 'center',
  },
  intervalLabel: {
    color: '#aaa',
    fontSize: 16,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#2a2a4a',
    borderRadius: 8,
    padding: 16,
  },
  switchLabel: {
    color: '#fff',
    fontSize: 16,
  },
  saveButton: {
    backgroundColor: '#ff6b35',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 12,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  logoutButton: {
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 16,
    borderWidth: 1,
    borderColor: '#ff4444',
  },
  logoutButtonText: {
    color: '#ff4444',
    fontSize: 16,
    fontWeight: '600',
  },
  spacer: {
    height: 40,
  },
});
