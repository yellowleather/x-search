/**
 * Shared utility functions for the X Likes Capture extension
 */

/**
 * Get authentication state from storage
 * @returns {Promise<Object|null>} Auth object or null if not authenticated
 */
async function getAuthState() {
  const result = await chrome.storage.local.get(['auth']);
  return result.auth || null;
}

/**
 * Save authentication state to storage
 * @param {Object} auth - Auth object with tokens and user info
 */
async function saveAuthState(auth) {
  await chrome.storage.local.set({ auth });
}

/**
 * Clear authentication state
 */
async function clearAuth() {
  await chrome.storage.local.remove(['auth']);
}

/**
 * Get settings from storage
 * @returns {Promise<Object>} Settings object with defaults
 */
async function getSettings() {
  const result = await chrome.storage.local.get(['settings']);
  return {
    backendUrl: 'https://tweet-capture-api-423049276532.us-central1.run.app',
    captureEnabled: true,
    ...result.settings
  };
}

/**
 * Save settings to storage
 * @param {Object} settings - Settings object
 */
async function saveSettings(settings) {
  await chrome.storage.local.set({ settings });
}

/**
 * Get stats from storage
 * @returns {Promise<Object>} Stats object
 */
async function getStats() {
  const result = await chrome.storage.local.get(['stats']);
  return result.stats || {
    totalCaptured: 0,
    totalSent: 0,
    queueSize: 0,
    lastCapture: null,
    lastSync: null
  };
}

/**
 * Update stats in storage
 * @param {string} action - Type of update ('captured', 'sent', 'queued')
 */
async function updateStats(action) {
  const stats = await getStats();
  const now = Date.now();

  switch (action) {
    case 'captured':
      stats.totalCaptured++;
      stats.lastCapture = now;
      break;
    case 'sent':
      stats.totalSent++;
      stats.lastSync = now;
      break;
    case 'queued':
      stats.queueSize++;
      break;
  }

  await chrome.storage.local.set({ stats });
}

/**
 * Format timestamp as "X mins/hours/days ago"
 * @param {number|Date} timestamp - Timestamp to format
 * @returns {string} Formatted time string
 */
function formatTimeAgo(timestamp) {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'Just now';

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min${minutes > 1 ? 's' : ''} ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days > 1 ? 's' : ''} ago`;

  const months = Math.floor(days / 30);
  return `${months} month${months > 1 ? 's' : ''} ago`;
}

/**
 * Check if access token is expired or about to expire
 * @param {number} expiresAt - Expiry timestamp
 * @param {number} bufferSeconds - Buffer time before expiry (default 60s)
 * @returns {boolean} True if expired or expiring soon
 */
function isTokenExpired(expiresAt, bufferSeconds = 60) {
  return Date.now() >= (expiresAt - (bufferSeconds * 1000));
}

/**
 * Show notification to user
 * @param {string} message - Notification message
 * @param {string} type - Notification type ('info', 'success', 'error')
 */
async function showNotification(message, type = 'info') {
  // For Chrome extensions, we could use chrome.notifications
  // For now, we'll just log and could show in popup
  console.log(`[${type.toUpperCase()}] ${message}`);

  // Store last notification for popup to display
  await chrome.storage.local.set({
    lastNotification: {
      message,
      type,
      timestamp: Date.now()
    }
  });
}

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid email format
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Sanitize tweet text (remove potential XSS vectors)
 * @param {string} text - Text to sanitize
 * @returns {string} Sanitized text
 */
function sanitizeText(text) {
  if (!text) return '';
  return text.replace(/[<>]/g, '');
}

/**
 * Extract tweet ID from URL
 * @param {string} url - Tweet URL
 * @returns {string|null} Tweet ID or null
 */
function extractTweetId(url) {
  const match = url.match(/status\/(\d+)/);
  return match ? match[1] : null;
}

/**
 * Debug logger (only logs if debug mode enabled)
 * @param {...any} args - Arguments to log
 */
function debugLog(...args) {
  // Check if debug mode is enabled in settings
  chrome.storage.local.get(['settings'], (result) => {
    if (result.settings?.debugMode) {
      console.log('[X Likes Capture]', ...args);
    }
  });
}

/**
 * Handle API errors and convert to user-friendly messages
 * @param {Error} error - Error object
 * @returns {string} User-friendly error message
 */
function getErrorMessage(error) {
  if (!error) return 'An unknown error occurred';

  if (error.message) {
    if (error.message.includes('Failed to fetch')) {
      return 'Unable to connect to server. Please check your internet connection.';
    }
    if (error.message.includes('NetworkError')) {
      return 'Network error. Please try again.';
    }
  }

  if (error.status) {
    switch (error.status) {
      case 401:
        return 'Authentication failed. Please log in again.';
      case 403:
        return 'Access denied.';
      case 404:
        return 'Server endpoint not found.';
      case 429:
        return 'Too many requests. Please wait a moment.';
      case 500:
        return 'Server error. Please try again later.';
      case 503:
        return 'Service temporarily unavailable.';
      default:
        return `Server error (${error.status})`;
    }
  }

  return error.message || 'An error occurred';
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getAuthState,
    saveAuthState,
    clearAuth,
    getSettings,
    saveSettings,
    getStats,
    updateStats,
    formatTimeAgo,
    isTokenExpired,
    showNotification,
    isValidEmail,
    sanitizeText,
    extractTweetId,
    debugLog,
    getErrorMessage
  };
}
