/**
 * Login Screen
 * Token entry and validation
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { REGIONS } from '../constants/config';

export default function LoginScreen({ onLogin, initialRegion = 'na' }) {
  const [accessToken, setAccessToken] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [region, setRegion] = useState(initialRegion);
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!accessToken.trim()) {
      Alert.alert('Error', 'Please enter your access token');
      return;
    }

    setLoading(true);
    try {
      const result = await onLogin(accessToken.trim(), refreshToken.trim() || null, region);
      if (!result.valid) {
        Alert.alert('Token Invalid', result.error || 'Could not validate token');
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.header}>
          <Text style={styles.title}>Flex Monitor</Text>
          <Text style={styles.subtitle}>Enter your Amazon Flex tokens</Text>
        </View>

        <View style={styles.form}>
          <Text style={styles.label}>Region</Text>
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

          <Text style={styles.label}>Access Token *</Text>
          <TextInput
            style={styles.input}
            value={accessToken}
            onChangeText={setAccessToken}
            placeholder="Paste your x-amz-access-token"
            placeholderTextColor="#999"
            multiline
            numberOfLines={4}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <Text style={styles.label}>Refresh Token (optional)</Text>
          <TextInput
            style={styles.input}
            value={refreshToken}
            onChangeText={setRefreshToken}
            placeholder="Paste your refresh token"
            placeholderTextColor="#999"
            multiline
            numberOfLines={2}
            autoCapitalize="none"
            autoCorrect={false}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Connect</Text>
            )}
          </TouchableOpacity>

          <View style={styles.helpContainer}>
            <Text style={styles.helpTitle}>How to get your token:</Text>
            <Text style={styles.helpText}>
              1. Use mitmproxy to capture traffic from Amazon Flex app
            </Text>
            <Text style={styles.helpText}>
              2. Look for requests to flex-capacity-*.amazon.com
            </Text>
            <Text style={styles.helpText}>
              3. Copy the x-amz-access-token header value
            </Text>
          </View>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  scrollContent: {
    flexGrow: 1,
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginTop: 60,
    marginBottom: 40,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#aaa',
  },
  form: {
    flex: 1,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#fff',
    marginBottom: 8,
    marginTop: 16,
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
    fontSize: 14,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  button: {
    backgroundColor: '#ff6b35',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  helpContainer: {
    marginTop: 32,
    padding: 16,
    backgroundColor: '#2a2a4a',
    borderRadius: 8,
  },
  helpTitle: {
    color: '#fff',
    fontWeight: '600',
    marginBottom: 12,
  },
  helpText: {
    color: '#aaa',
    fontSize: 13,
    marginBottom: 6,
    lineHeight: 20,
  },
});
