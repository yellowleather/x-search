# FEATURE SPECIFICATION: X Likes Capture Chrome Extension

## PROJECT OVERVIEW
Build a secure, privacy-first Chrome extension (Manifest V3) that automatically captures tweet metadata when users like tweets on X.com (Twitter). The extension authenticates users via JWT tokens, queues tweets offline, and syncs to a backend API. Designed for personal knowledge management with zero-trust architecture - no API keys or service accounts stored in the extension.

## EXTENSION PURPOSE

**Core Responsibilities:**
1. Monitor X.com DOM for user like actions
2. Extract tweet metadata (text, author, timestamp, context)
3. Authenticate users via JWT-based backend API
4. Queue tweets locally when offline or not authenticated
5. Sync queued tweets to backend when online
6. Provide user interface for auth, stats, and settings

**Non-Responsibilities (Out of Scope):**
- Tweet enrichment or analysis (handled by backend)
- Cloud storage (extension only stores JWTs and queue)
- Multi-account management (single user focus)
- Analytics or tracking (privacy-first)

## ARCHITECTURE OVERVIEW
```
┌─────────────────────────────────────────────────────────────────────┐
│  X.com / Twitter.com                                                │
│  (User browses and likes tweets)                                    │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ DOM Events (click on like button)
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Content Script (content.js)                                        │
│  • Monitors DOM for like button clicks                              │
│  • Extracts tweet metadata from DOM                                 │
│  • Sends to background worker via chrome.runtime.sendMessage        │
└────────────────┬────────────────────────────────────────────────────┘
                 │
                 │ chrome.runtime.sendMessage({ action: 'captureTweet' })
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Background Service Worker (background.js)                          │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Authentication Manager                                      │   │
│  │ • Stores JWT tokens (access + refresh)                     │   │
│  │ • Auto-refreshes expired tokens                            │   │
│  │ • Handles login/logout                                     │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ Queue Manager                                               │   │
│  │ • Queues tweets when offline/not authenticated             │   │
│  │ • Retries failed syncs                                     │   │
│  │ • Manages local storage queue                              │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ API Client                                                  │   │
│  │ • Sends tweets to backend                                  │   │
│  │ • Handles auth endpoints (login, register, refresh)        │   │
│  │ • Error handling and retry logic                           │   │
│  └────────────────┬───────────────────────────────────────────┘   │
└───────────────────┼───────────────────────────────────────────────┘
                    │
                    │ HTTPS POST /api/tweets/capture
                    │ Authorization: Bearer <JWT>
                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Backend API (FastAPI / Cloud Run)                                  │
│  • Validates JWT                                                    │
│  • Stores tweets in Firestore                                      │
│  • Publishes to Pub/Sub for processing                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Popup UI (popup.html/js)                                           │
│  • Login/Register interface                                         │
│  • Display stats (captured, synced, queued)                         │
│  • Manual retry button                                              │
│  • Link to settings                                                 │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  Options Page (options.html/js)                                     │
│  • Configure backend URL                                            │
│  • Test connection                                                  │
│  • Enable/disable auto-capture                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Architectural Decisions:**
- **Manifest V3**: Latest Chrome extension standard (required for future)
- **Service Worker**: Background.js runs as service worker (no persistent background page)
- **Zero-Trust**: No service accounts or API keys in extension
- **Offline-First**: Queue tweets locally, sync when online
- **JWT-Based Auth**: Short-lived access tokens (1 hour), long-lived refresh tokens (30 days)

## TECHNOLOGY STACK

### Extension Platform
- **Manifest Version**: V3 (latest Chrome standard)
- **Browser**: Chrome, Edge, Brave (Chromium-based)
- **Storage**: chrome.storage.local (encrypted by browser)
- **Messaging**: chrome.runtime.sendMessage (content ↔ background)

### Programming
- **Language**: Vanilla JavaScript (ES6+)
- **DOM Manipulation**: Native DOM APIs (no jQuery)
- **Testing**: Jest + jsdom + Testing Library
- **Module System**: CommonJS (for tests) + Browser globals (for extension)

### Why This Stack?
- **Vanilla JS**: No build step, no bundling, simple deployment
- **Manifest V3**: Future-proof, required for Chrome Web Store
- **chrome.storage.local**: Encrypted by browser, simple API
- **Zero dependencies**: Fast, secure, no supply chain risk

### Testing Stack (package.json)
```json
{
  "devDependencies": {
    "@babel/core": "^7.23.5",
    "@babel/preset-env": "^7.23.5",
    "@testing-library/dom": "^9.3.3",
    "@testing-library/jest-dom": "^6.1.5",
    "babel-jest": "^29.7.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0"
  }
}
```

## COMPONENT SPECIFICATIONS

### 1. Content Script (content.js)

**Purpose**: Monitor X.com DOM for like actions and extract tweet metadata

**Initialization:**
```javascript
function init() {
  console.log('[X Likes Capture] Content script loaded');

  // Monitor for like button clicks
  document.addEventListener('click', handleClick, true);

  // Use MutationObserver for dynamic content
  observeLikeButtons();
}
```

**Like Detection Logic:**
1. Listen for click events on entire document (capture phase)
2. Traverse up from clicked element to find like button
3. Check `data-testid="like"` attribute
4. Find parent tweet article element
5. Extract tweet metadata
6. Send to background worker

**Tweet Extraction Logic:**
```javascript
function extractTweetData(tweetArticle) {
  return {
    tweetId: extractTweetId(tweetArticle),        // From tweet URL
    tweetUrl: extractTweetUrl(tweetArticle),      // Full tweet link
    tweetText: extractTweetText(tweetArticle),    // Text content
    authorUsername: extractAuthorUsername(tweetArticle),
    authorDisplayName: extractAuthorDisplayName(tweetArticle),
    timestamp: extractTimestamp(tweetArticle),    // ISO 8601
    capturedAt: Date.now(),                       // Capture timestamp

    // Context flags
    isReply: isReplyTweet(tweetArticle),
    isRetweet: isRetweetTweet(tweetArticle),
    isQuoteTweet: isQuoteTweet(tweetArticle),
    isThread: isThreadTweet(tweetArticle),
    threadId: extractThreadId(tweetArticle),
    parentTweetId: extractParentTweetId(tweetArticle),
    conversationId: extractConversationId(tweetArticle),

    // Media indicators
    hasImage: hasImageMedia(tweetArticle),
    hasVideo: hasVideoMedia(tweetArticle),
    hasLink: hasLinkInTweet(tweetArticle)
  };
}
```

**DOM Selectors (X.com specific):**
- Tweet article: `article[data-testid="tweet"]`
- Like button: `button[data-testid="like"]` or `button[data-testid="unlike"]`
- Tweet text: `div[data-testid="tweetText"]`
- Author username: `a[role="link"]` with `/` href pattern
- Timestamp: `time` element with `datetime` attribute
- Media: `div[data-testid="tweetPhoto"]`, `div[data-testid="videoPlayer"]`

**Deduplication:**
- Track processed tweet IDs in Set: `processedTweets`
- Clear Set periodically to avoid memory leak
- Tweet ID is unique identifier

**Visual Feedback:**
```javascript
function showCaptureIndicator(tweetArticle) {
  // Show brief checkmark overlay on tweet
  const indicator = document.createElement('div');
  indicator.textContent = '✓ Captured';
  indicator.style.cssText = 'position:absolute;top:10px;right:10px;...';
  tweetArticle.appendChild(indicator);

  setTimeout(() => indicator.remove(), 2000);
}
```

**Edge Cases:**
- Handle promoted tweets (skip)
- Handle deleted/unavailable tweets
- Handle tweets with restricted content
- Handle rapid like/unlike actions (debounce)

### 2. Background Service Worker (background.js)

**Purpose**: Handle authentication, API communication, and queue management

**Imports:**
```javascript
// Import shared utilities (Service Worker compatible)
importScripts('utils.js');
```

**Message Handler:**
```javascript
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case 'captureTweet':
      handleCaptureTweet(message.data)
        .then(() => sendResponse({ success: true }))
        .catch(error => sendResponse({ success: false, error: error.message }));
      return true; // Keep channel open for async

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
```

**Tweet Capture Flow:**
```javascript
async function handleCaptureTweet(tweetData) {
  // 1. Update stats
  await updateStats('captured');

  // 2. Check authentication
  const auth = await getAuthState();
  if (!auth || !auth.accessToken) {
    await queueTweet(tweetData);
    await showNotification('Please log in to sync tweets', 'info');
    return;
  }

  // 3. Check token expiry
  if (isTokenExpired(auth.expiresAt)) {
    try {
      await refreshAccessToken();
    } catch (error) {
      await queueTweet(tweetData);
      await showNotification('Session expired. Please log in again.', 'error');
      return;
    }
  }

  // 4. Send to backend
  try {
    const updatedAuth = await getAuthState();
    await sendToBackend(tweetData, updatedAuth.accessToken);
    await updateStats('sent');
  } catch (error) {
    if (error.status === 401) {
      // Token invalid, try refresh once
      try {
        await refreshAccessToken();
        const refreshedAuth = await getAuthState();
        await sendToBackend(tweetData, refreshedAuth.accessToken);
        await updateStats('sent');
      } catch (retryError) {
        await queueTweet(tweetData);
        await showNotification('Failed to sync tweet. Queued for retry.', 'error');
      }
    } else {
      // Network error, queue for retry
      await queueTweet(tweetData);
      await showNotification('Network error. Tweet queued for retry.', 'error');
    }
  }
}
```

**API Communication:**
```javascript
async function sendToBackend(tweetData, accessToken) {
  const settings = await getSettings();

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
    throw error;
  }

  return await response.json();
}
```

**Token Refresh:**
```javascript
async function refreshAccessToken() {
  const auth = await getAuthState();
  const settings = await getSettings();

  if (!auth || !auth.refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await fetch(`${settings.backendUrl}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refreshToken: auth.refreshToken })
  });

  if (!response.ok) {
    throw new Error('Token refresh failed');
  }

  const data = await response.json();

  // Update auth state with new access token
  await saveAuthState({
    ...auth,
    accessToken: data.accessToken,
    expiresAt: Date.now() + (data.expiresIn * 1000)
  });
}
```

**Queue Management:**
```javascript
async function queueTweet(tweetData) {
  const queue = await getQueue();
  queue.push({
    id: generateId(),
    tweet: tweetData,
    queuedAt: Date.now(),
    attempts: 0
  });
  await saveQueue(queue);
  await updateStats('queued');
}

async function retryQueue() {
  const queue = await getQueue();
  const auth = await getAuthState();

  if (!auth || !auth.accessToken) {
    return { error: 'Not authenticated' };
  }

  const results = {
    processed: 0,
    succeeded: 0,
    failed: 0
  };

  const remainingQueue = [];

  for (const item of queue) {
    results.processed++;

    try {
      await sendToBackend(item.tweet, auth.accessToken);
      results.succeeded++;
      await updateStats('sent');
    } catch (error) {
      item.attempts++;

      if (item.attempts < 5) {
        remainingQueue.push(item);
      }

      results.failed++;
    }
  }

  await saveQueue(remainingQueue);
  await updateQueueStats();

  return results;
}
```

**Periodic Sync (via alarms):**
```javascript
// Set up periodic sync
chrome.alarms.create('syncQueue', { periodInMinutes: 30 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'syncQueue') {
    retryQueue().catch(console.error);
  }
});
```

### 3. Popup Interface (popup.html/js)

**Purpose**: User interface for authentication and status display

**HTML Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>X Likes Capture</title>
  <link rel="stylesheet" href="popup.css">
</head>
<body>
  <!-- Not authenticated view -->
  <div id="auth-container" class="hidden">
    <h2>X Likes Capture</h2>

    <!-- Login form -->
    <div id="login-form">
      <input type="email" id="email" placeholder="Email">
      <input type="password" id="password" placeholder="Password">
      <button id="login-btn">Log In</button>
      <a href="#" id="show-register">Create account</a>
    </div>

    <!-- Register form -->
    <div id="register-form" class="hidden">
      <input type="email" id="reg-email" placeholder="Email">
      <input type="password" id="reg-password" placeholder="Password">
      <button id="register-btn">Create Account</button>
      <a href="#" id="show-login">Back to login</a>
    </div>
  </div>

  <!-- Authenticated view -->
  <div id="main-container" class="hidden">
    <h2>X Likes Capture</h2>

    <!-- Stats -->
    <div class="stats">
      <div class="stat-item">
        <span class="stat-value" id="total-captured">0</span>
        <span class="stat-label">Captured</span>
      </div>
      <div class="stat-item">
        <span class="stat-value" id="total-synced">0</span>
        <span class="stat-label">Synced</span>
      </div>
      <div class="stat-item">
        <span class="stat-value" id="queue-size">0</span>
        <span class="stat-label">Queued</span>
      </div>
    </div>

    <!-- Last activity -->
    <div class="activity">
      <p>Last capture: <span id="last-capture">Never</span></p>
      <p>Last sync: <span id="last-sync">Never</span></p>
    </div>

    <!-- Actions -->
    <div class="actions">
      <button id="retry-btn" class="action-btn">
        Retry Queue (<span id="retry-count">0</span>)
      </button>
      <button id="settings-btn" class="action-btn">Settings</button>
      <button id="logout-btn" class="action-btn logout">Log Out</button>
    </div>
  </div>

  <script src="utils.js"></script>
  <script src="popup.js"></script>
</body>
</html>
```

**JavaScript Logic (popup.js):**
```javascript
// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
  await checkAuthAndRender();
  setupEventListeners();

  if (await isAuthenticated()) {
    await updateStats();

    // Update stats every 5 seconds
    setInterval(updateStats, 5000);
  }
});

async function checkAuthAndRender() {
  const auth = await getAuthState();

  if (auth && auth.accessToken) {
    // Show authenticated view
    document.getElementById('auth-container').classList.add('hidden');
    document.getElementById('main-container').classList.remove('hidden');
  } else {
    // Show login view
    document.getElementById('auth-container').classList.remove('hidden');
    document.getElementById('main-container').classList.add('hidden');
  }
}

async function updateStats() {
  const stats = await getStats();

  document.getElementById('total-captured').textContent = stats.totalCaptured;
  document.getElementById('total-synced').textContent = stats.totalSent;
  document.getElementById('queue-size').textContent = stats.queueSize;
  document.getElementById('retry-count').textContent = stats.queueSize;

  if (stats.lastCapture) {
    document.getElementById('last-capture').textContent =
      formatTimeAgo(stats.lastCapture);
  }

  if (stats.lastSync) {
    document.getElementById('last-sync').textContent =
      formatTimeAgo(stats.lastSync);
  }
}

function setupEventListeners() {
  // Login
  document.getElementById('login-btn').addEventListener('click', handleLogin);

  // Register
  document.getElementById('register-btn').addEventListener('click', handleRegister);

  // Toggle forms
  document.getElementById('show-register').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
  });

  document.getElementById('show-login').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('login-form').classList.remove('hidden');
  });

  // Retry queue
  document.getElementById('retry-btn').addEventListener('click', handleRetryQueue);

  // Settings
  document.getElementById('settings-btn').addEventListener('click', () => {
    chrome.runtime.openOptionsPage();
  });

  // Logout
  document.getElementById('logout-btn').addEventListener('click', handleLogout);
}

async function handleLogin() {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;

  if (!email || !password) {
    showError('Please enter email and password');
    return;
  }

  try {
    const settings = await getSettings();

    const response = await fetch(`${settings.backendUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();

    // Save auth state
    await saveAuthState({
      userId: data.userId,
      email: data.email,
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      expiresAt: Date.now() + (data.expiresIn * 1000)
    });

    // Refresh UI
    await checkAuthAndRender();
    await updateStats();

  } catch (error) {
    showError(error.message);
  }
}

async function handleRegister() {
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;

  if (!email || !password) {
    showError('Please enter email and password');
    return;
  }

  if (password.length < 8) {
    showError('Password must be at least 8 characters');
    return;
  }

  try {
    const settings = await getSettings();

    const response = await fetch(`${settings.backendUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();

    // Save auth state
    await saveAuthState({
      userId: data.userId,
      email: data.email,
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      expiresAt: Date.now() + (data.expiresIn * 1000)
    });

    // Refresh UI
    await checkAuthAndRender();
    await updateStats();

  } catch (error) {
    showError(error.message);
  }
}

async function handleRetryQueue() {
  const button = document.getElementById('retry-btn');
  button.disabled = true;
  button.textContent = 'Retrying...';

  try {
    const result = await chrome.runtime.sendMessage({ action: 'retryQueue' });

    if (result.error) {
      throw new Error(result.error);
    }

    await updateStats();
    showSuccess(`Synced ${result.succeeded} tweets`);

  } catch (error) {
    showError(error.message);
  } finally {
    button.disabled = false;
    await updateStats();
    const queue = await getStats();
    button.textContent = `Retry Queue (${queue.queueSize})`;
  }
}

async function handleLogout() {
  await clearAuth();
  await checkAuthAndRender();
}

function showError(message) {
  // Show error toast
  const toast = document.createElement('div');
  toast.className = 'toast error';
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 3000);
}

function showSuccess(message) {
  // Show success toast
  const toast = document.createElement('div');
  toast.className = 'toast success';
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 3000);
}
```

### 4. Options Page (options.html/js)

**Purpose**: Configure extension settings

**HTML Structure:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>X Likes Capture - Settings</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      max-width: 600px;
      margin: 40px auto;
      padding: 20px;
    }
    .setting-group {
      margin-bottom: 30px;
    }
    label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
    }
    input[type="text"] {
      width: 100%;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    button {
      padding: 8px 16px;
      background: #1d9bf0;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    button:hover {
      background: #1a8cd8;
    }
    .status {
      margin-top: 10px;
      padding: 10px;
      border-radius: 4px;
    }
    .status.success {
      background: #d4edda;
      color: #155724;
    }
    .status.error {
      background: #f8d7da;
      color: #721c24;
    }
  </style>
</head>
<body>
  <h1>X Likes Capture - Settings</h1>

  <div class="setting-group">
    <label for="backend-url">Backend API URL</label>
    <input type="text" id="backend-url" placeholder="https://api.yourservice.com">
    <button id="test-connection">Test Connection</button>
    <div id="connection-status"></div>
  </div>

  <div class="setting-group">
    <label>
      <input type="checkbox" id="capture-enabled" checked>
      Enable automatic capture
    </label>
  </div>

  <button id="save-settings">Save Settings</button>

  <div id="save-status"></div>

  <script src="utils.js"></script>
  <script src="options.js"></script>
</body>
</html>
```

**JavaScript Logic (options.js):**
```javascript
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  setupEventListeners();
});

async function loadSettings() {
  const settings = await getSettings();

  document.getElementById('backend-url').value = settings.backendUrl;
  document.getElementById('capture-enabled').checked = settings.captureEnabled;
}

function setupEventListeners() {
  document.getElementById('test-connection').addEventListener('click', testConnection);
  document.getElementById('save-settings').addEventListener('click', saveSettingsHandler);
}

async function testConnection() {
  const url = document.getElementById('backend-url').value;
  const statusEl = document.getElementById('connection-status');

  statusEl.textContent = 'Testing...';
  statusEl.className = 'status';

  try {
    const response = await fetch(`${url}/api/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error('Connection failed');
    }

    const data = await response.json();

    statusEl.textContent = `✓ Connected to ${data.version || 'backend'}`;
    statusEl.className = 'status success';

  } catch (error) {
    statusEl.textContent = `✗ Connection failed: ${error.message}`;
    statusEl.className = 'status error';
  }
}

async function saveSettingsHandler() {
  const settings = {
    backendUrl: document.getElementById('backend-url').value,
    captureEnabled: document.getElementById('capture-enabled').checked
  };

  await saveSettings(settings);

  const statusEl = document.getElementById('save-status');
  statusEl.textContent = '✓ Settings saved';
  statusEl.className = 'status success';

  setTimeout(() => {
    statusEl.textContent = '';
    statusEl.className = '';
  }, 3000);
}
```

### 5. Shared Utilities (utils.js)

**Purpose**: Shared functions used across content, background, and popup

**Storage Functions:**
```javascript
// Authentication
async function getAuthState() {
  const result = await chrome.storage.local.get(['auth']);
  return result.auth || null;
}

async function saveAuthState(auth) {
  await chrome.storage.local.set({ auth });
}

async function clearAuth() {
  await chrome.storage.local.remove(['auth']);
}

async function isAuthenticated() {
  const auth = await getAuthState();
  return !!(auth && auth.accessToken);
}

// Settings
async function getSettings() {
  const result = await chrome.storage.local.get(['settings']);
  return {
    backendUrl: 'https://api.yourservice.com',
    captureEnabled: true,
    ...result.settings
  };
}

async function saveSettings(settings) {
  await chrome.storage.local.set({ settings });
}

// Stats
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
      if (stats.queueSize > 0) stats.queueSize--;
      break;
    case 'queued':
      stats.queueSize++;
      break;
  }

  await chrome.storage.local.set({ stats });
}

// Queue
async function getQueue() {
  const result = await chrome.storage.local.get(['queue']);
  return result.queue || [];
}

async function saveQueue(queue) {
  await chrome.storage.local.set({ queue });
}

async function updateQueueStats() {
  const queue = await getQueue();
  const stats = await getStats();
  stats.queueSize = queue.length;
  await chrome.storage.local.set({ stats });
}
```

**Helper Functions:**
```javascript
// Token expiry check
function isTokenExpired(expiresAt) {
  if (!expiresAt) return true;
  // Add 5 minute buffer
  return Date.now() >= (expiresAt - (5 * 60 * 1000));
}

// Format time ago
function formatTimeAgo(timestamp) {
  const date = timestamp instanceof Date ? timestamp : new Date(timestamp);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)} mins ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
  return `${Math.floor(seconds / 86400)} days ago`;
}

// Generate unique ID
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// Debug logging
function debugLog(...args) {
  if (typeof console !== 'undefined') {
    console.log('[X Likes Capture]', ...args);
  }
}
```

**Module Exports (for testing):**
```javascript
// Export for testing (CommonJS)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getAuthState,
    saveAuthState,
    clearAuth,
    isAuthenticated,
    getSettings,
    saveSettings,
    getStats,
    updateStats,
    getQueue,
    saveQueue,
    isTokenExpired,
    formatTimeAgo,
    generateId,
    debugLog
  };
}
```

## DATA MODELS

### Auth State (chrome.storage.local)
```javascript
{
  "auth": {
    "userId": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "refresh_abc123xyz...",
    "expiresAt": 1700395800000  // Unix timestamp
  }
}
```

### Settings (chrome.storage.local)
```javascript
{
  "settings": {
    "backendUrl": "https://tweet-capture-api-xyz.run.app",
    "captureEnabled": true
  }
}
```

### Stats (chrome.storage.local)
```javascript
{
  "stats": {
    "totalCaptured": 150,
    "totalSent": 145,
    "queueSize": 5,
    "lastCapture": 1700395800000,
    "lastSync": 1700395700000
  }
}
```

### Queue (chrome.storage.local)
```javascript
{
  "queue": [
    {
      "id": "l9k8j7h6g5f4",
      "tweet": {
        "tweetId": "1234567890123456789",
        "tweetUrl": "https://x.com/user/status/1234567890123456789",
        "tweetText": "This is a tweet...",
        "authorUsername": "username",
        "authorDisplayName": "Display Name",
        "timestamp": "2024-11-19T10:30:00.000Z",
        "capturedAt": 1700395800000,
        "isReply": false,
        "isRetweet": false,
        "isQuoteTweet": false,
        "isThread": false,
        "threadId": null,
        "parentTweetId": null,
        "conversationId": "1234567890123456789",
        "hasImage": true,
        "hasVideo": false,
        "hasLink": false
      },
      "queuedAt": 1700395800000,
      "attempts": 2
    }
  ]
}
```

### Tweet Data Model (sent to backend)
```javascript
{
  "tweetId": "1234567890123456789",
  "tweetUrl": "https://x.com/username/status/1234567890123456789",
  "tweetText": "This is the tweet content...",
  "authorUsername": "username",
  "authorDisplayName": "Display Name",
  "timestamp": "2024-11-19T10:30:00Z",
  "capturedAt": 1700395800000,

  // Context flags
  "isReply": false,
  "isRetweet": false,
  "isQuoteTweet": false,
  "isThread": false,
  "threadId": null,
  "parentTweetId": null,
  "conversationId": "1234567890123456789",

  // Media indicators
  "hasImage": true,
  "hasVideo": false,
  "hasLink": false
}
```

## API INTEGRATION

### Backend API Endpoints

**POST /api/auth/register**
```javascript
// Request
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

// Response 201
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "accessToken": "eyJhbGci...",
  "refreshToken": "refresh_...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**POST /api/auth/login**
```javascript
// Request
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}

// Response 200
{
  "userId": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "accessToken": "eyJhbGci...",
  "refreshToken": "refresh_...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**POST /api/auth/refresh**
```javascript
// Request
{
  "refreshToken": "refresh_abc123xyz..."
}

// Response 200
{
  "accessToken": "eyJhbGci...",
  "expiresIn": 3600,
  "tokenType": "Bearer"
}
```

**POST /api/tweets/capture**
```javascript
// Request Headers
Authorization: Bearer eyJhbGci...
Content-Type: application/json

// Request Body
{
  "tweetId": "1234567890123456789",
  "tweetUrl": "https://x.com/user/status/1234567890123456789",
  "tweetText": "Tweet content...",
  "authorUsername": "username",
  "authorDisplayName": "Display Name",
  "timestamp": "2024-11-19T10:30:00Z",
  "capturedAt": 1700395800000,
  "isReply": false,
  "isRetweet": false,
  "isQuoteTweet": false,
  "isThread": false,
  "threadId": null,
  "parentTweetId": null,
  "conversationId": "1234567890123456789",
  "hasImage": false,
  "hasVideo": false,
  "hasLink": false
}

// Response 200 (Success)
{
  "status": "published",
  "tweetId": "1234567890123456789",
  "messageId": "projects/my-project/topics/tweet-likes-raw/messages/123"
}

// Response 200 (Duplicate)
{
  "status": "duplicate",
  "tweetId": "1234567890123456789",
  "message": "Tweet already captured"
}

// Response 401 (Unauthorized)
{
  "detail": "Invalid or expired token"
}
```

**GET /api/health**
```javascript
// Response 200
{
  "status": "healthy",
  "timestamp": "2024-11-19T10:30:00Z",
  "services": {
    "firestore": "connected",
    "pubsub": "connected"
  },
  "version": "1.0.0"
}
```

## PROJECT STRUCTURE

```
src/chrome_extension/
├── 📄 Manifest & Core
│   ├── manifest.json              # Extension manifest (Manifest V3)
│   ├── content.js                # Content script (~400 lines)
│   ├── background.js             # Service worker (~350 lines)
│   └── utils.js                  # Shared utilities (~220 lines)
│
├── 🎨 User Interface
│   ├── popup.html                # Extension popup UI
│   ├── popup.js                  # Popup logic (~470 lines)
│   ├── popup.css                 # Popup styles
│   ├── options.html              # Settings page
│   └── options.js                # Settings logic (~345 lines)
│
├── 🖼️ Icons
│   └── icons/
│       ├── icon16.png            # 16x16 toolbar icon
│       ├── icon48.png            # 48x48 management icon
│       └── icon128.png           # 128x128 Chrome Web Store icon
│
├── 🧪 Testing
│   ├── __tests__/
│   │   ├── unit/
│   │   │   ├── utils.test.js     # Utils unit tests
│   │   │   └── content.test.js   # Content script tests
│   │   ├── helpers.js            # Test utilities
│   │   └── setup.js              # Jest setup
│   ├── jest.config.js            # Jest configuration
│   ├── .babelrc                  # Babel config (for Jest)
│   └── package.json              # Test dependencies
│
├── 🔧 Test Backend
│   └── test_backend/
│       ├── server.js             # Mock backend API
│       ├── package.json          # Backend dependencies
│       └── README.md             # Backend docs
│
└── 📖 Documentation
    └── README.md                 # Complete documentation
```

## TESTING STRATEGY

### Unit Tests (Jest + jsdom)

**Test Setup (jest.config.js):**
```javascript
module.exports = {
  testEnvironment: 'jsdom',

  // Transform JS files with Babel
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Setup file for global mocks
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],

  // Coverage configuration
  collectCoverageFrom: [
    'utils.js',
    'content.js',
    '!background.js',  // Exclude (needs integration tests)
    '!popup.js',       // Exclude (needs integration tests)
    '!options.js',     // Exclude (needs integration tests)
    '!**/__tests__/**',
    '!**/node_modules/**',
    '!**/test_backend/**'
  ],

  coverageThreshold: {
    './utils.js': {
      branches: 80,
      functions: 80,
      lines: 88,
      statements: 89
    },
    './content.js': {
      branches: 40,
      functions: 40,
      lines: 50,
      statements: 50
    }
  },

  testMatch: [
    '**/__tests__/**/*.test.js'
  ]
};
```

**Test Setup (__tests__/setup.js):**
```javascript
// Mock Chrome APIs
global.chrome = {
  storage: {
    local: {
      get: jest.fn(),
      set: jest.fn(),
      remove: jest.fn()
    }
  },
  runtime: {
    sendMessage: jest.fn(),
    onMessage: {
      addListener: jest.fn()
    },
    lastError: null
  },
  alarms: {
    create: jest.fn(),
    onAlarm: {
      addListener: jest.fn()
    }
  }
};

// Reset mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
});
```

**Test Helpers (__tests__/helpers.js):**
```javascript
// Create mock tweet article DOM
function createMockTweetArticle(options = {}) {
  const {
    tweetId = '1234567890123456789',
    tweetText = 'This is a test tweet',
    authorUsername = 'testuser',
    authorDisplayName = 'Test User',
    timestamp = '2024-11-19T10:30:00.000Z',
    isReply = false,
    hasImage = false
  } = options;

  const article = document.createElement('article');
  article.setAttribute('data-testid', 'tweet');

  // Tweet text
  const textDiv = document.createElement('div');
  textDiv.setAttribute('data-testid', 'tweetText');
  textDiv.textContent = tweetText;
  article.appendChild(textDiv);

  // Author link
  const authorLink = document.createElement('a');
  authorLink.href = `/${authorUsername}`;
  authorLink.textContent = authorDisplayName;
  article.appendChild(authorLink);

  // Timestamp
  const time = document.createElement('time');
  time.setAttribute('datetime', timestamp);
  article.appendChild(time);

  // Tweet link
  const tweetLink = document.createElement('a');
  tweetLink.href = `/${authorUsername}/status/${tweetId}`;
  article.appendChild(tweetLink);

  // Like button
  const likeButton = document.createElement('button');
  likeButton.setAttribute('data-testid', 'like');
  article.appendChild(likeButton);

  return article;
}

// Create mock auth state
function createMockAuthState(options = {}) {
  return {
    userId: options.userId || 'user_123',
    email: options.email || 'test@example.com',
    accessToken: options.accessToken || 'mock_access_token',
    refreshToken: options.refreshToken || 'mock_refresh_token',
    expiresAt: options.expiresAt || Date.now() + 3600000
  };
}

// Mock Chrome storage get
function mockStorageGet(data) {
  global.chrome.storage.local.get.mockImplementation((keys, callback) => {
    const result = typeof keys === 'string' ? { [keys]: data } : data;
    if (callback) callback(result);
    return Promise.resolve(result);
  });
}

module.exports = {
  createMockTweetArticle,
  createMockAuthState,
  mockStorageGet
};
```

**Example Tests (__tests__/unit/utils.test.js):**
```javascript
const {
  getAuthState,
  saveAuthState,
  isTokenExpired,
  formatTimeAgo
} = require('../../utils.js');

describe('utils.js', () => {
  describe('getAuthState', () => {
    it('should return auth from storage', async () => {
      const mockAuth = { userId: '123', accessToken: 'token' };
      chrome.storage.local.get.mockResolvedValue({ auth: mockAuth });

      const result = await getAuthState();

      expect(result).toEqual(mockAuth);
      expect(chrome.storage.local.get).toHaveBeenCalledWith(['auth']);
    });

    it('should return null if no auth', async () => {
      chrome.storage.local.get.mockResolvedValue({});

      const result = await getAuthState();

      expect(result).toBeNull();
    });
  });

  describe('isTokenExpired', () => {
    it('should return true for expired token', () => {
      const expiredTime = Date.now() - 10000;
      expect(isTokenExpired(expiredTime)).toBe(true);
    });

    it('should return false for valid token', () => {
      const validTime = Date.now() + 3600000;
      expect(isTokenExpired(validTime)).toBe(false);
    });

    it('should return true for null expiry', () => {
      expect(isTokenExpired(null)).toBe(true);
    });
  });

  describe('formatTimeAgo', () => {
    it('should format seconds as "Just now"', () => {
      const now = Date.now();
      expect(formatTimeAgo(now)).toBe('Just now');
    });

    it('should format minutes', () => {
      const fiveMinsAgo = Date.now() - (5 * 60 * 1000);
      expect(formatTimeAgo(fiveMinsAgo)).toBe('5 mins ago');
    });

    it('should format hours', () => {
      const twoHoursAgo = Date.now() - (2 * 60 * 60 * 1000);
      expect(formatTimeAgo(twoHoursAgo)).toBe('2 hours ago');
    });
  });
});
```

### Test Coverage Goals

- **utils.js**: 88%+ coverage (all helper functions)
- **content.js**: 50%+ coverage (DOM extraction logic)
- **background.js**: Integration tests (E2E with test backend)
- **popup.js**: Integration tests (E2E with test backend)
- **options.js**: Integration tests (E2E with test backend)

### Test Backend (test_backend/server.js)

**Purpose**: Mock backend API for manual testing and E2E tests

```javascript
const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.use(express.json());

// In-memory storage
const users = new Map();
const tweets = new Map();
let sessionCounter = 0;

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0-test'
  });
});

// Register
app.post('/api/auth/register', (req, res) => {
  const { email, password } = req.body;

  if (users.has(email)) {
    return res.status(409).json({ detail: 'Email already registered' });
  }

  const userId = `user_${sessionCounter++}`;
  users.set(email, { userId, email, password });

  res.status(201).json({
    userId,
    email,
    accessToken: `access_${userId}`,
    refreshToken: `refresh_${userId}`,
    expiresIn: 3600,
    tokenType: 'Bearer'
  });
});

// Login
app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;

  const user = users.get(email);
  if (!user || user.password !== password) {
    return res.status(401).json({ detail: 'Invalid email or password' });
  }

  res.json({
    userId: user.userId,
    email: user.email,
    accessToken: `access_${user.userId}`,
    refreshToken: `refresh_${user.userId}`,
    expiresIn: 3600,
    tokenType: 'Bearer'
  });
});

// Refresh token
app.post('/api/auth/refresh', (req, res) => {
  const { refreshToken } = req.body;

  if (!refreshToken || !refreshToken.startsWith('refresh_')) {
    return res.status(401).json({ detail: 'Invalid refresh token' });
  }

  const userId = refreshToken.replace('refresh_', '');

  res.json({
    accessToken: `access_${userId}_refreshed`,
    expiresIn: 3600,
    tokenType: 'Bearer'
  });
});

// Capture tweet
app.post('/api/tweets/capture', (req, res) => {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ detail: 'Missing or invalid authorization' });
  }

  const tweetData = req.body;
  const tweetId = tweetData.tweetId;

  if (tweets.has(tweetId)) {
    return res.json({
      status: 'duplicate',
      tweetId,
      message: 'Tweet already captured'
    });
  }

  tweets.set(tweetId, tweetData);

  console.log('✓ Tweet captured:', tweetId, '-', tweetData.tweetText.substring(0, 50));

  res.json({
    status: 'published',
    tweetId,
    messageId: `mock_message_${Date.now()}`
  });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log('🚀 X Likes Capture - Test Backend API');
  console.log(`📡 Server running on: http://localhost:${PORT}`);
  console.log('');
  console.log('Endpoints:');
  console.log('  GET  /api/health');
  console.log('  POST /api/auth/register');
  console.log('  POST /api/auth/login');
  console.log('  POST /api/auth/refresh');
  console.log('  POST /api/tweets/capture');
});
```

## SECURITY BEST PRACTICES

### Zero-Trust Architecture
- **NO service accounts** in extension
- **NO API keys** in extension
- **Only JWT tokens** (short-lived access + long-lived refresh)
- All sensitive operations happen server-side

### Data Storage
- Use `chrome.storage.local` (encrypted by browser)
- Never store passwords
- Store only JWTs and user preferences
- Clear auth on logout

### Token Management
- Access tokens: 1 hour expiry
- Refresh tokens: 30 day expiry
- Auto-refresh before expiry (5 min buffer)
- Clear tokens on 401 errors

### Network Security
- HTTPS only (enforced by Manifest V3)
- Validate backend URL format
- Handle network errors gracefully
- No inline scripts (CSP compliant)

### Content Security Policy
```json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'"
  }
}
```

### Permissions (Minimal)
```json
{
  "permissions": [
    "storage",   // Only for chrome.storage.local
    "alarms"     // Only for periodic sync
  ],
  "host_permissions": [
    "https://x.com/*",
    "https://twitter.com/*"
  ]
}
```

### Input Validation
- Validate all user inputs (email, password, URL)
- Sanitize DOM-extracted data
- Validate backend responses
- Handle malformed data gracefully

## INSTALLATION & DEPLOYMENT

### Development Setup

**Prerequisites:**
```bash
# Node.js 14+ for testing
node --version  # v14+

# Chrome or Chromium-based browser
```

**Setup:**
```bash
cd src/chrome_extension

# Install test dependencies
npm install

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Start test backend
cd test_backend
npm install
npm start
```

**Load Extension:**
1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select `src/chrome_extension` folder

### Chrome Web Store Publishing

**Prepare for Publishing:**
1. Create high-quality icons (16x16, 48x48, 128x128)
2. Update manifest.json with final name and description
3. Create promotional images (1280x800, 440x280, 640x400)
4. Write comprehensive privacy policy
5. Create ZIP package: `zip -r extension.zip . -x "*/node_modules/*" "*/test_backend/*" "*/.git/*"`

**Publishing Steps:**
1. Create Chrome Web Store developer account ($5 one-time fee)
2. Upload ZIP package
3. Fill in store listing:
   - Detailed description
   - Screenshots
   - Privacy policy
   - Category: Productivity
4. Submit for review (1-3 days)

**Privacy Policy Requirements:**
- Explain data collection (tweet metadata only)
- Explain data usage (personal knowledge management)
- Explain data sharing (sent to user's own backend)
- No tracking or analytics
- No third-party data sharing

### Updating the Extension

**For Users:**
- Extensions auto-update from Chrome Web Store
- Or manually update via Developer mode

**For Developers:**
```bash
# Increment version in manifest.json
# Test thoroughly
npm test

# Create new ZIP package
zip -r extension-v1.1.0.zip . -x "*/node_modules/*" "*/test_backend/*"

# Upload to Chrome Web Store
# Submit for review
```

## DELIVERABLES

Generate complete, production-ready code for:

### Core Extension Files
1. **manifest.json** - Manifest V3 configuration
2. **content.js** - DOM monitoring and tweet extraction (~400 lines)
3. **background.js** - Service worker with auth and queue (~350 lines)
4. **utils.js** - Shared utility functions (~220 lines)

### User Interface
5. **popup.html** - Extension popup interface
6. **popup.js** - Popup logic with auth and stats (~470 lines)
7. **popup.css** - Popup styles
8. **options.html** - Settings page
9. **options.js** - Settings logic (~345 lines)

### Testing
10. **jest.config.js** - Jest configuration
11. **.babelrc** - Babel configuration for Jest
12. **package.json** - Test dependencies
13. **__tests__/setup.js** - Jest setup and Chrome API mocks
14. **__tests__/helpers.js** - Test utilities
15. **__tests__/unit/utils.test.js** - Utils unit tests
16. **__tests__/unit/content.test.js** - Content script tests

### Test Backend
17. **test_backend/server.js** - Mock backend API
18. **test_backend/package.json** - Backend dependencies
19. **test_backend/README.md** - Backend documentation

### Documentation
20. **README.md** - Complete user and developer documentation

### Assets
21. **icons/icon16.png** - 16x16 toolbar icon
22. **icons/icon48.png** - 48x48 management icon
23. **icons/icon128.png** - 128x128 Chrome Web Store icon

## CODE QUALITY STANDARDS

- **Vanilla JavaScript**: No frameworks, no build step
- **ES6+**: Modern JavaScript features (async/await, arrow functions, destructuring)
- **Modularity**: Separate concerns (content, background, UI, utils)
- **Error Handling**: Try-catch blocks, graceful degradation
- **Logging**: Consistent debug logging with prefix `[X Likes Capture]`
- **Comments**: Document complex logic and DOM selectors
- **Testing**: Unit tests for utils and content extraction
- **Browser Compatibility**: Chrome 88+ (Manifest V3 requirement)
- **Performance**: Minimal DOM queries, debounced event handlers
- **Security**: No eval(), no inline scripts, CSP compliant

## EDGE CASES & ERROR HANDLING

### Content Script Edge Cases
- Handle promoted tweets (skip them)
- Handle deleted/unavailable tweets
- Handle tweets with restricted content
- Handle rapid like/unlike (debounce)
- Handle dynamic X.com UI changes
- Handle multiple tabs with X.com open

### Background Worker Edge Cases
- Handle offline mode (queue tweets)
- Handle token expiry during request
- Handle network errors (retry with exponential backoff)
- Handle backend downtime (queue for later)
- Handle invalid backend responses
- Handle quota exceeded errors

### UI Edge Cases
- Handle invalid email format
- Handle weak passwords
- Handle invalid backend URL
- Handle connection failures
- Handle empty queue
- Handle concurrent auth requests

### Storage Edge Cases
- Handle storage quota exceeded
- Handle corrupted storage data
- Handle missing storage keys
- Handle concurrent storage writes

## MANIFEST V3 COMPLIANCE

**Required Changes from V2:**
- ✅ Service worker instead of background page
- ✅ `importScripts()` instead of `<script>` tags
- ✅ `chrome.alarms` for periodic tasks (no `setInterval`)
- ✅ Declarative content security policy
- ✅ Host permissions separate from permissions
- ✅ No remotely hosted code
- ✅ No `eval()` or `new Function()`

**Best Practices:**
- Keep service worker logic minimal
- Use chrome.alarms for periodic sync (not setInterval)
- Handle service worker wake/sleep cycles
- Minimize storage usage
- Use message passing efficiently

---

**OUTPUT REQUIREMENT**: Generate complete, production-ready Chrome Extension (Manifest V3) that:
1. Automatically captures tweet metadata when users like tweets on X.com
2. Authenticates users via JWT-based backend API
3. Queues tweets offline and syncs when online
4. Provides user interface for auth, stats, and settings
5. Includes comprehensive unit tests (Jest + jsdom)
6. Includes test backend for manual testing
7. Follows zero-trust architecture (no API keys in extension)
8. Is privacy-first (no tracking, no analytics)
9. Is ready for Chrome Web Store publishing
10. Includes complete documentation for users and developers

**Extension Name**: X Likes Capture
**Manifest Version**: 3 (latest Chrome standard)
**Browser Support**: Chrome, Edge, Brave (Chromium-based)
**Privacy**: Zero tracking, no analytics, user-owned data
**Cost**: Free to install and use
