/**
 * Background Service Worker for X Likes Capture Extension
 * Handles authentication, API communication, and queue management
 */

// Import utility functions
importScripts('utils.js');

/**
 * Message handler from content script and popup
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  debugLog('Received message:', message.action);

  switch (message.action) {
    case 'captureTweet':
      handleCaptureTweet(message.data)
        .then(() => sendResponse({ success: true }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true; // Keep channel open for async response

    case 'retryQueue':
      retryQueue()
        .then(result => sendResponse(result))
        .catch(error => sendResponse({ error: error.message }));
      return true;

    case 'getAuthStatus':
      getAuthState()
        .then(auth => sendResponse({ authenticated: !!auth, auth }))
        .catch(error => sendResponse({ error: error.message }));
      return true;

    default:
      sendResponse({ error: 'Unknown action' });
  }
});

/**
 * Handle tweet capture from content script
 * @param {Object} tweetData - Tweet metadata
 */
async function handleCaptureTweet(tweetData) {
  debugLog('Handling tweet capture:', tweetData.tweetId);

  // Update stats - captured
  await updateStats('captured');

  // Check if authenticated
  const auth = await getAuthState();
  if (!auth || !auth.accessToken) {
    debugLog('Not authenticated, queuing tweet');
    await queueTweet(tweetData);
    await showNotification('Please log in to sync tweets', 'info');
    return;
  }

  // Check token expiry
  if (isTokenExpired(auth.expiresAt)) {
    debugLog('Token expired, refreshing...');
    try {
      await refreshAccessToken();
    } catch (error) {
      debugLog('Token refresh failed:', error);
      await queueTweet(tweetData);
      await showNotification('Session expired. Please log in again.', 'error');
      return;
    }
  }

  // Send to backend
  try {
    const updatedAuth = await getAuthState();
    await sendToBackend(tweetData, updatedAuth.accessToken);
    await updateStats('sent');
    debugLog('Tweet sent successfully:', tweetData.tweetId);
  } catch (error) {
    debugLog('Send failed:', error);

    if (error.status === 401) {
      // Token invalid, try refresh once
      try {
        await refreshAccessToken();
        const refreshedAuth = await getAuthState();
        await sendToBackend(tweetData, refreshedAuth.accessToken);
        await updateStats('sent');
      } catch (retryError) {
        // Refresh or retry failed, queue it
        await queueTweet(tweetData);
        await showNotification('Failed to sync tweet. Queued for retry.', 'error');
      }
    } else {
      // Network error or other issue, queue for retry
      await queueTweet(tweetData);
      await showNotification('Network error. Tweet queued for retry.', 'error');
    }
  }
}

/**
 * Send tweet data to backend API
 * @param {Object} tweetData - Tweet metadata
 * @param {string} accessToken - JWT access token
 */
async function sendToBackend(tweetData, accessToken) {
  const settings = await getSettings();

  debugLog('Sending to backend:', settings.backendUrl);

  const response = await fetch(`${settings.backendUrl}/api/tweets/capture`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(tweetData)
  });

  if (!response.ok) {
    const error = new Error('Backend request failed');
    error.status = response.status;

    try {
      const errorData = await response.json();
      error.message = errorData.error || error.message;
    } catch (e) {
      // Response not JSON
    }

    throw error;
  }

  return await response.json();
}

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken() {
  const auth = await getAuthState();
  const settings = await getSettings();

  if (!auth || !auth.refreshToken) {
    throw new Error('No refresh token available');
  }

  debugLog('Refreshing access token...');

  const response = await fetch(`${settings.backendUrl}/api/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      refreshToken: auth.refreshToken
    })
  });

  if (!response.ok) {
    // Refresh failed, clear auth and show login
    await clearAuth();
    await showNotification('Session expired. Please log in again.', 'error');
    throw new Error('Token refresh failed');
  }

  const data = await response.json();

  // Update auth state with new tokens
  await saveAuthState({
    accessToken: data.accessToken,
    refreshToken: data.refreshToken || auth.refreshToken,
    expiresAt: Date.now() + (data.expiresIn * 1000),
    userId: auth.userId,
    email: auth.email
  });

  debugLog('Token refreshed successfully');
}

/**
 * Add tweet to local queue for retry
 * @param {Object} tweetData - Tweet metadata
 */
async function queueTweet(tweetData) {
  const storage = await chrome.storage.local.get(['queue']);
  const queue = storage.queue || [];

  // Check if tweet already in queue
  const existingIndex = queue.findIndex(
    item => item.tweetData.tweetId === tweetData.tweetId
  );

  if (existingIndex !== -1) {
    debugLog('Tweet already in queue:', tweetData.tweetId);
    return;
  }

  // Add to queue with retry metadata
  queue.push({
    tweetData,
    attempts: 0,
    queuedAt: Date.now(),
    lastAttempt: null,
    error: null
  });

  // Limit queue size (keep last 500)
  if (queue.length > 500) {
    queue.shift();
  }

  await chrome.storage.local.set({ queue });
  await updateStats('queued');

  debugLog('Tweet queued:', tweetData.tweetId, 'Queue size:', queue.length);
}

/**
 * Retry sending queued tweets
 * @returns {Object} Result with processed and remaining counts
 */
async function retryQueue() {
  const storage = await chrome.storage.local.get(['queue', 'auth']);
  const queue = storage.queue || [];
  const auth = storage.auth;

  if (!auth || !auth.accessToken) {
    debugLog('Cannot retry queue: not authenticated');
    return { processed: 0, remaining: queue.length };
  }

  debugLog('Retrying queue, size:', queue.length);

  const successfullyProcessed = [];

  for (const item of queue) {
    // Skip after 3 failures
    if (item.attempts >= 3) {
      debugLog('Skipping item after 3 attempts:', item.tweetData.tweetId);
      continue;
    }

    try {
      // Check token expiry before each attempt
      const currentAuth = await getAuthState();
      if (isTokenExpired(currentAuth.expiresAt)) {
        await refreshAccessToken();
      }

      const freshAuth = await getAuthState();
      await sendToBackend(item.tweetData, freshAuth.accessToken);

      successfullyProcessed.push(item);
      await updateStats('sent');
      debugLog('Queue item sent successfully:', item.tweetData.tweetId);

    } catch (error) {
      item.attempts++;
      item.lastAttempt = Date.now();
      item.error = error.message;
      debugLog('Queue item failed:', item.tweetData.tweetId, error.message);
    }
  }

  // Remove successfully processed items
  const remainingQueue = queue.filter(
    item => !successfullyProcessed.includes(item)
  );

  await chrome.storage.local.set({ queue: remainingQueue });

  // Update queue size in stats
  const stats = await getStats();
  stats.queueSize = remainingQueue.length;
  await chrome.storage.local.set({ stats });

  const result = {
    processed: successfullyProcessed.length,
    remaining: remainingQueue.length
  };

  debugLog('Queue retry complete:', result);

  if (result.processed > 0) {
    await showNotification(
      `Successfully synced ${result.processed} tweet(s)`,
      'success'
    );
  }

  return result;
}

/**
 * Set up periodic queue retry alarm
 */
chrome.runtime.onInstalled.addListener(() => {
  debugLog('Extension installed/updated, setting up alarms');

  // Create alarm for periodic queue retry (every 5 minutes)
  chrome.alarms.create('retryQueue', { periodInMinutes: 5 });

  // Initialize default settings
  getSettings().then(settings => {
    debugLog('Settings initialized:', settings);
  });
});

/**
 * Handle alarm events
 */
chrome.alarms.onAlarm.addListener((alarm) => {
  debugLog('Alarm triggered:', alarm.name);

  if (alarm.name === 'retryQueue') {
    retryQueue().catch(error => {
      debugLog('Automatic queue retry failed:', error);
    });
  }
});

/**
 * Handle extension startup
 */
chrome.runtime.onStartup.addListener(() => {
  debugLog('Extension started');

  // Try to sync queue on startup
  retryQueue().catch(error => {
    debugLog('Startup queue retry failed:', error);
  });
});

/**
 * Check backend health
 * @param {string} backendUrl - Backend API URL
 * @returns {Promise<boolean>} True if backend is healthy
 */
async function checkBackendHealth(backendUrl) {
  try {
    const response = await fetch(`${backendUrl}/api/health`, {
      method: 'GET'
    });
    return response.ok;
  } catch (error) {
    debugLog('Backend health check failed:', error);
    return false;
  }
}

debugLog('Background service worker loaded');
