# FEATURE SPECIFICATION: X Liked Tweets Capture Chrome Extension (Secure Backend API)

## PROJECT OVERVIEW
Build a secure Chrome extension that captures tweets when a user likes them on X.com and sends to your backend API using JWT authentication. The extension stores NO secrets - only short-lived user tokens.

## SECURITY ARCHITECTURE
```
┌─────────────────────────────────────────────────────────────┐
│ Chrome Extension (Zero Trust Client)                         │
│ • Captures tweet metadata only                               │
│ • Stores: JWT token (1 hour expiry) + refresh token         │
│ • NO service accounts, NO API keys, NO secrets              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ POST /api/tweets/capture
                            │ Authorization: Bearer <JWT>
                            │ Body: { tweetData }
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ Your Backend API (Trust Boundary)                            │
│ • Validates JWT signature                                    │
│ • Extracts user_id from token                               │
│ • Rate limits per user                                       │
│ • Has service account credentials (environment variable)    │
│ • Publishes to Pub/Sub with service account                 │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            │ Service account publishes
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ Google Cloud Pub/Sub                                         │
│ • Receives messages from backend only                        │
│ • Extension has NO access to this layer                     │
└─────────────────────────────────────────────────────────────┘
```

## TECHNICAL REQUIREMENTS

### Extension Architecture
- **Manifest Version**: V3
- **Target Platform**: Chrome Desktop Browser
- **Target Website**: x.com and twitter.com
- **Primary Language**: JavaScript (ES6+)
- **External Dependency**: Your Backend API (JWT-based)

### Core Components

#### 1. Manifest File (manifest.json)
```json
{
  "manifest_version": 3,
  "name": "X Likes Capture",
  "version": "1.0.0",
  "description": "Securely captures your liked tweets for personal knowledge management",
  "permissions": [
    "storage"
  ],
  "host_permissions": [
    "https://x.com/*",
    "https://twitter.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["https://x.com/*", "https://twitter.com/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

**Note**: No `identity` permission needed, no access to external APIs except your backend.

#### 2. Content Script (content.js)

**Purpose**: Monitor X's DOM for like actions and extract metadata (unchanged from previous spec)

**Data Structure to Capture:**
```javascript
{
  // Core identifiers
  tweetId: "1234567890123456789",
  tweetUrl: "https://x.com/user/status/1234567890123456789",
  
  // Content
  tweetText: "Full tweet text...",
  
  // Author info
  authorUsername: "username",
  authorDisplayName: "Display Name",
  
  // Timestamps
  timestamp: "2024-11-19T10:30:00Z",     // When tweet was posted
  capturedAt: 1700395800000,             // When we captured it
  
  // Context flags
  isReply: false,
  isRetweet: false,
  isQuoteTweet: false,
  isThread: false,
  
  // Thread/conversation context
  threadId: "1234567890123456789",       // Root tweet ID
  parentTweetId: null,                    // If reply
  conversationId: "1234567890123456789",
  
  // Media indicators
  hasImage: false,
  hasVideo: false,
  hasLink: false
}
```

**Implementation** (same as before):
```javascript
// Monitor for like button state change
// When button transitions from data-testid="like" to "unlike"
// Extract tweet data and send to background worker

chrome.runtime.sendMessage({
  action: 'captureTweet',
  data: tweetData
});
```

#### 3. Background Service Worker (background.js)

**Purpose**: Manage authentication and communicate with backend API

**Key Responsibilities:**
- Receive captured tweets from content script
- Check authentication status
- Add auth headers to requests
- Handle token refresh
- Retry failed requests
- Maintain local queue for offline scenarios

**Authentication State Management:**
```javascript
// Stored in chrome.storage.local (encrypted by Chrome)
{
  auth: {
    accessToken: "eyJhbGciOiJIUzI1NiIs...",  // JWT, expires in 1 hour
    refreshToken: "refresh_abc123...",        // Expires in 30 days
    expiresAt: 1700398800000,                 // Unix timestamp
    userId: "user-uuid-here",
    email: "user@example.com"
  },
  settings: {
    backendUrl: "https://api.yourservice.com",  // Configurable
    captureEnabled: true
  },
  queue: [
    // Tweets that failed to send (offline/error)
  ],
  stats: {
    totalCaptured: 0,
    totalSent: 0,
    queueSize: 0,
    lastCapture: null,
    lastSync: null
  }
}
```

**Core Functions:**
```javascript
// 1. Message handler from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'captureTweet') {
    handleCaptureTweet(message.data)
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ success: false, error: error.message }));
    return true; // Keep channel open for async response
  }
});

// 2. Capture and send to backend
async function handleCaptureTweet(tweetData) {
  // Check if authenticated
  const auth = await getAuthState();
  if (!auth || !auth.accessToken) {
    // Queue locally, show login prompt
    await queueTweet(tweetData);
    await showNotification('Please log in to sync tweets');
    return;
  }
  
  // Check token expiry
  if (Date.now() >= auth.expiresAt) {
    await refreshAccessToken();
  }
  
  // Send to backend
  try {
    await sendToBackend(tweetData, auth.accessToken);
    await updateStats('sent');
  } catch (error) {
    if (error.status === 401) {
      // Token invalid, try refresh
      await refreshAccessToken();
      await sendToBackend(tweetData, auth.accessToken);
    } else {
      // Network error, queue for retry
      await queueTweet(tweetData);
      throw error;
    }
  }
}

// 3. Send to backend API
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

// 4. Token refresh
async function refreshAccessToken() {
  const auth = await getAuthState();
  const settings = await getSettings();
  
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
    throw new Error('Session expired, please log in again');
  }
  
  const data = await response.json();
  await saveAuthState({
    accessToken: data.accessToken,
    refreshToken: data.refreshToken || auth.refreshToken,
    expiresAt: Date.now() + (data.expiresIn * 1000),
    userId: auth.userId,
    email: auth.email
  });
}

// 5. Local queue management
async function queueTweet(tweetData) {
  const storage = await chrome.storage.local.get(['queue']);
  const queue = storage.queue || [];
  
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
}

// 6. Retry queued tweets (called periodically or manually)
async function retryQueue() {
  const storage = await chrome.storage.local.get(['queue', 'auth']);
  const queue = storage.queue || [];
  const auth = storage.auth;
  
  if (!auth || !auth.accessToken) {
    return; // Can't retry without auth
  }
  
  const successfullyProcessed = [];
  
  for (const item of queue) {
    if (item.attempts >= 3) {
      continue; // Skip after 3 failures
    }
    
    try {
      await sendToBackend(item.tweetData, auth.accessToken);
      successfullyProcessed.push(item);
      item.attempts++;
    } catch (error) {
      item.attempts++;
      item.lastAttempt = Date.now();
      item.error = error.message;
    }
  }
  
  // Remove successfully processed items
  const remainingQueue = queue.filter(
    item => !successfullyProcessed.includes(item)
  );
  
  await chrome.storage.local.set({ queue: remainingQueue });
  
  return {
    processed: successfullyProcessed.length,
    remaining: remainingQueue.length
  };
}
```

**Background Tasks:**
```javascript
// Set up periodic queue retry (every 5 minutes)
chrome.alarms.create('retryQueue', { periodInMinutes: 5 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'retryQueue') {
    retryQueue().catch(console.error);
  }
});
```

#### 4. Popup Interface (popup.html + popup.js)

**Purpose**: Authentication UI and status dashboard

**UI States:**

**State 1: Not Authenticated**
```html
┌─────────────────────────────────┐
│ 🔐 X Likes Capture              │
├─────────────────────────────────┤
│ Welcome! Please log in to start │
│ capturing your liked tweets.    │
│                                 │
│ Email:                          │
│ [____________________]          │
│                                 │
│ Password:                       │
│ [____________________]          │
│                                 │
│ [Login]  [Register]             │
│                                 │
│ Backend: ✅ Connected           │
│ api.yourservice.com             │
└─────────────────────────────────┘
```

**State 2: Authenticated - Active**
```html
┌─────────────────────────────────┐
│ 📊 X Likes Capture              │
├─────────────────────────────────┤
│ Logged in as: user@example.com  │
│ Status: ✅ Active               │
│                                 │
│ Today:                          │
│ • Captured: 12 tweets           │
│ • Synced: 12 tweets             │
│ • Queued: 0 tweets              │
│                                 │
│ Last capture: 2 mins ago        │
│ Last sync: 2 mins ago           │
│                                 │
│ [Retry Queue] [Settings]        │
│ [Logout]                        │
└─────────────────────────────────┘
```

**State 3: Authenticated - Offline/Queued**
```html
┌─────────────────────────────────┐
│ ⚠️ X Likes Capture              │
├─────────────────────────────────┤
│ Logged in as: user@example.com  │
│ Status: ⚠️ Offline/Queued       │
│                                 │
│ Queued tweets: 5                │
│ Will sync when online           │
│                                 │
│ [Retry Now] [View Queue]        │
│ [Settings] [Logout]             │
└─────────────────────────────────┘
```

**popup.js - Key Functions:**
```javascript
// Initialize popup based on auth state
document.addEventListener('DOMContentLoaded', async () => {
  const auth = await chrome.storage.local.get(['auth']);
  
  if (auth.auth && auth.auth.accessToken) {
    showAuthenticatedView();
    loadStats();
  } else {
    showLoginView();
  }
});

// Handle login
document.getElementById('loginBtn').addEventListener('click', async () => {
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  
  try {
    const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) {
      throw new Error('Invalid credentials');
    }
    
    const data = await response.json();
    
    // Save auth state
    await chrome.storage.local.set({
      auth: {
        accessToken: data.accessToken,
        refreshToken: data.refreshToken,
        expiresAt: Date.now() + (data.expiresIn * 1000),
        userId: data.userId,
        email: email
      }
    });
    
    showAuthenticatedView();
    
    // Retry any queued tweets
    chrome.runtime.sendMessage({ action: 'retryQueue' });
    
  } catch (error) {
    document.getElementById('error').textContent = error.message;
  }
});

// Handle logout
document.getElementById('logoutBtn').addEventListener('click', async () => {
  await chrome.storage.local.remove(['auth']);
  showLoginView();
});

// Load and display stats
async function loadStats() {
  const stats = await chrome.storage.local.get(['stats', 'queue']);
  
  document.getElementById('capturedCount').textContent = stats.stats?.totalCaptured || 0;
  document.getElementById('syncedCount').textContent = stats.stats?.totalSent || 0;
  document.getElementById('queuedCount').textContent = stats.queue?.length || 0;
  
  if (stats.stats?.lastCapture) {
    const lastCapture = new Date(stats.stats.lastCapture);
    document.getElementById('lastCapture').textContent = formatTimeAgo(lastCapture);
  }
}

// Retry queue button
document.getElementById('retryBtn').addEventListener('click', async () => {
  document.getElementById('retryBtn').disabled = true;
  document.getElementById('retryBtn').textContent = 'Retrying...';
  
  const result = await chrome.runtime.sendMessage({ action: 'retryQueue' });
  
  alert(`Processed: ${result.processed}, Remaining: ${result.remaining}`);
  
  loadStats();
  document.getElementById('retryBtn').disabled = false;
  document.getElementById('retryBtn').textContent = 'Retry Queue';
});
```

#### 5. Settings/Options Page (options.html + options.js)

**Purpose**: Advanced configuration
```html
┌────────────────────────────────────┐
│ ⚙️ Settings                        │
├────────────────────────────────────┤
│ Backend API Configuration          │
│                                    │
│ API URL:                           │
│ [https://api.yourservice.com____]  │
│ [Test Connection]                  │
│                                    │
│ Capture Settings                   │
│ ☑ Auto-capture likes               │
│ ☐ Capture bookmarks too (future)   │
│ ☐ Capture full threads            │
│                                    │
│ Data Management                    │
│ Local queue: 5 tweets              │
│ [Export Queue] [Clear Queue]       │
│                                    │
│ [Save Settings]                    │
└────────────────────────────────────┘
```

#### 6. Styling (popup.css)

**Design Principles:**
- Clean, modern interface
- Clear visual states (logged in/out, online/offline)
- Status indicators with color coding:
  - Green (✅) = Active and syncing
  - Yellow (⚠️) = Queued/offline
  - Red (❌) = Error/not authenticated
- Responsive to popup size constraints
- Accessible (ARIA labels, keyboard navigation)

## BACKEND API CONTRACT

**The extension expects these endpoints from your backend:**

### POST /api/auth/register
```json
Request:
{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response: 201 Created
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "refresh_abc123...",
  "expiresIn": 3600,
  "userId": "uuid-here"
}
```

### POST /api/auth/login
```json
Request:
{
  "email": "user@example.com",
  "password": "securepassword123"
}

Response: 200 OK
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "refresh_abc123...",
  "expiresIn": 3600,
  "userId": "uuid-here"
}

Error: 401 Unauthorized
{
  "error": "Invalid credentials"
}
```

### POST /api/auth/refresh
```json
Request:
{
  "refreshToken": "refresh_abc123..."
}

Response: 200 OK
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "expiresIn": 3600
}

Error: 401 Unauthorized
{
  "error": "Invalid refresh token"
}
```

### POST /api/tweets/capture
```json
Request Headers:
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

Request Body:
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
  "threadId": "1234567890123456789",
  "parentTweetId": null,
  "conversationId": "1234567890123456789",
  "hasImage": false,
  "hasVideo": false,
  "hasLink": false
}

Response: 200 OK
{
  "status": "queued",
  "tweetId": "1234567890123456789",
  "messageId": "pubsub-message-id"
}

Error: 401 Unauthorized
{
  "error": "Invalid or expired token"
}

Error: 429 Too Many Requests
{
  "error": "Rate limit exceeded",
  "retryAfter": 60
}
```

### GET /api/health (Optional)
```json
Response: 200 OK
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## SECURITY FEATURES

**What the extension NEVER stores:**
- ❌ Service account credentials
- ❌ API keys for third-party services
- ❌ Passwords (only used during login, never stored)
- ❌ Long-lived tokens

**What the extension DOES store:**
- ✅ JWT access token (1 hour expiry)
- ✅ Refresh token (30 days expiry, revocable)
- ✅ User email (for display purposes)
- ✅ Backend URL (configurable)

**Token Security:**
- Stored in `chrome.storage.local` (encrypted by Chrome)
- Cleared on logout
- Automatically refreshed before expiry
- Validated on server for every request
- Can be revoked by user via backend

**Network Security:**
- All requests over HTTPS only
- No credentials in URL parameters
- Authorization header for bearer token
- CORS properly configured

## ERROR HANDLING

**Authentication Errors:**
```javascript
// 401 during capture → Try refresh token
// Refresh fails → Clear auth, show login
// Network error during login → Show friendly message
```

**Network Errors:**
```javascript
// No internet → Queue locally, show offline status
// Server down → Queue locally, retry later
// Timeout → Retry with exponential backoff
```

**Rate Limiting:**
```javascript
// 429 response → Show message, respect Retry-After header
// Queue additional requests
```

**Storage Errors:**
```javascript
// Quota exceeded → Warn user, offer to export queue
// Clear old stats to free space
```

## IMPLEMENTATION CHECKLIST

**Phase 1: Authentication**
- [ ] Create login/register UI
- [ ] Implement JWT storage and retrieval
- [ ] Implement token refresh logic
- [ ] Handle authentication errors
- [ ] Add logout functionality

**Phase 2: Tweet Capture**
- [ ] Implement DOM monitoring (same as before)
- [ ] Extract tweet metadata
- [ ] Send to background worker
- [ ] Display capture confirmation

**Phase 3: Backend Communication**
- [ ] Implement sendToBackend with auth headers
- [ ] Handle 401 (token refresh)
- [ ] Handle network errors (queue)
- [ ] Implement retry logic

**Phase 4: Queue Management**
- [ ] Implement local queue
- [ ] Implement retry mechanism
- [ ] Add manual retry button
- [ ] Display queue status in popup

**Phase 5: UI/UX Polish**
- [ ] Show appropriate UI state (logged in/out)
- [ ] Display real-time stats
- [ ] Add loading indicators
- [ ] Add error messages
- [ ] Add success confirmations

**Phase 6: Testing**
- [ ] Test login/logout flow
- [ ] Test token refresh
- [ ] Test offline queuing
- [ ] Test retry logic
- [ ] Test various tweet types
- [ ] Test rate limiting handling

## DELIVERABLES

Generate complete, production-ready code:
1. **manifest.json** - Extension manifest
2. **content.js** - DOM monitoring and capture (~150 lines)
3. **background.js** - Auth management and API communication (~300 lines)
4. **popup.html** - Authentication and status UI
5. **popup.js** - Popup logic with auth flow (~250 lines)
6. **popup.css** - Clean, modern styling (~150 lines)
7. **options.html** - Settings page (optional)
8. **options.js** - Settings logic (optional)
9. **utils.js** - Shared utilities (auth, time formatting, etc.)
10. **README.md** - Installation guide and backend requirements
11. **icons/** - Extension icons

## CODE QUALITY STANDARDS

- Modern JavaScript (ES6+, async/await)
- JSDoc comments for public functions
- Comprehensive error handling with try-catch
- Clear user-facing error messages
- No console.log in production (use debug flag)
- Modular code (separate concerns)
- Functions under 50 lines
- Meaningful variable and function names

## TESTING SCENARIOS

**Authentication:**
- [ ] Register new user
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Token expiry and refresh
- [ ] Logout and state clearing

**Capture:**
- [ ] Like a regular tweet
- [ ] Like a reply
- [ ] Like a retweet
- [ ] Like a quote tweet
- [ ] Like a thread
- [ ] Unlike handling

**Offline/Network:**
- [ ] Capture while offline → queue
- [ ] Come back online → auto-retry
- [ ] Manual retry button
- [ ] Network timeout handling

**Edge Cases:**
- [ ] Rapid liking (10+ tweets quickly)
- [ ] Very long tweet text
- [ ] Special characters in tweet
- [ ] X UI changes (fallback selectors)

## FUTURE EXTENSIBILITY

Design to easily add:
- [ ] Bookmark capture (in addition to likes)
- [ ] Manual capture button (capture any tweet)
- [ ] Filter rules (only capture matching criteria)
- [ ] Full thread capture option
- [ ] Export queue to JSON
- [ ] View capture history in extension
- [ ] Multi-account support

---

**OUTPUT REQUIREMENT**: Generate complete, working Chrome extension code that:
1. Securely authenticates users with JWT tokens
2. Captures liked tweets from X.com
3. Sends to backend API with proper auth headers
4. Handles offline scenarios with local queue
5. Provides clear UI for authentication and status
6. Stores NO secrets or long-lived credentials
7. Can be loaded as unpacked extension and tested immediately

**Security Promise**: This extension maintains zero-trust architecture where the extension never has access to backend service credentials. All sensitive operations occur server-side behind JWT authentication.