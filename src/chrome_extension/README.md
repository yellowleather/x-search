# X Likes Capture Chrome Extension

A secure Chrome extension that automatically captures tweets when you like them on X.com (Twitter) and sends them to your backend API for personal knowledge management.

## 📚 Table of Contents

- [Quick Start](#-quick-start-5-minutes)
- [Security Architecture](#-security-architecture)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Testing Guide](#-complete-testing-guide)
- [Testing Strategy](#-testing-strategy)
- [Feature Specification](#-feature-specification)
- [Usage](#-usage)
- [Troubleshooting](#-troubleshooting)
- [Security Considerations](#-security-considerations)
- [Development](#-development)
- [Contributing](#-contributing)

---

## 🚀 Quick Start (5 Minutes)

Get up and running with X Likes Capture quickly!

### Prerequisites

- Chrome or Chromium-based browser
- Node.js (v14+) for test backend
- Active X.com (Twitter) account

### Step 1: Prepare Icons

Create placeholder icons for testing:

```bash
cd src/chrome_extension/icons

# Download placeholders (using curl)
curl "https://via.placeholder.com/16/1d9bf0/FFFFFF?text=X" -o icon16.png
curl "https://via.placeholder.com/48/1d9bf0/FFFFFF?text=X" -o icon48.png
curl "https://via.placeholder.com/128/1d9bf0/FFFFFF?text=X" -o icon128.png
```

### Step 2: Start Test Backend

```bash
cd test_backend
npm install
npm start
```

You should see:
```
🚀 X Likes Capture - Test Backend API
📡 Server running on: http://localhost:3000
```

### Step 3: Load Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right)
3. Click **Load unpacked**
4. Select the `chrome_extension` folder
5. Extension should now appear ✅

### Step 4: Configure & Authenticate

1. Click the extension icon
2. Go to Settings
3. Set Backend URL: `http://localhost:3000`
4. Click "Test Connection" → should show ✅
5. Save settings
6. Return to popup and register with `test@example.com` / `password123`

### Step 5: Test Capture

1. Visit [x.com](https://x.com) or [twitter.com](https://twitter.com)
2. Like any tweet ❤️
3. Look for a brief checkmark ✓ confirmation
4. Check extension popup - stats should show "Captured: 1 tweets"
5. Check backend terminal - should log the captured tweet

**🎉 Success!** Extension is working!

---

## 🔐 Security Architecture

This extension follows a **zero-trust architecture**:

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
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ Your Backend API (Trust Boundary)                            │
│ • Validates JWT signature                                    │
│ • Extracts user_id from token                               │
│ • Rate limits per user                                       │
│ • Has service account credentials (server-side only)        │
└─────────────────────────────────────────────────────────────┘
```

**Security Guarantees:**
- ✅ Stores only short-lived JWT tokens (1 hour expiry)
- ✅ No service account credentials
- ✅ No API keys
- ✅ All sensitive operations happen server-side
- ✅ Tokens stored in encrypted Chrome storage
- ✅ HTTPS-only communication

---

## ✨ Features

- **Automatic Capture**: Captures tweet metadata when you like a tweet
- **Secure Authentication**: JWT-based authentication with token refresh
- **Offline Support**: Queues tweets locally when offline, syncs when back online
- **Real-time Stats**: Track captured, synced, and queued tweets
- **Manual Retry**: Retry failed captures with one click
- **Configurable Backend**: Point to your own backend API
- **Privacy-First**: Only captures metadata, no tracking or analytics

### Captured Data

Each tweet includes:
- Tweet ID and URL
- Tweet text content
- Author username and display name
- Timestamp (when posted)
- Capture timestamp
- Context flags (reply, retweet, quote, thread)
- Media indicators (image, video, link)

---

## 📁 Project Structure

```
src/chrome_extension/
├── 📄 Core Extension Files
│   ├── manifest.json           # Extension manifest (V3)
│   ├── content.js             # DOM monitoring & tweet capture (~400 lines)
│   ├── background.js          # Service worker (auth & API) (~350 lines)
│   └── utils.js               # Shared utilities (~220 lines)
│
├── 🎨 UI Files
│   ├── popup.html             # Popup interface
│   ├── popup.js               # Popup logic (~470 lines)
│   ├── popup.css              # Popup styles
│   ├── options.html           # Settings page
│   └── options.js             # Settings logic (~345 lines)
│
├── 🖼️ Icons
│   └── icons/
│       ├── icon16.png         # 16x16 toolbar icon
│       ├── icon48.png         # 48x48 management icon
│       └── icon128.png        # 128x128 store icon
│
├── 🧪 Tests
│   ├── __tests__/
│   │   ├── unit/              # Unit tests (Jest)
│   │   ├── helpers.js         # Test utilities
│   │   └── setup.js           # Test configuration
│   ├── jest.config.js         # Jest configuration
│   └── package.json           # Test dependencies
│
└── 🔧 Test Backend
    └── test_backend/
        ├── server.js          # Mock backend API
        ├── package.json       # Backend dependencies
        └── README.md          # Backend documentation
```

### Key Components

**content.js** - Monitors X.com DOM for like actions
- Detects when user clicks like button
- Extracts tweet metadata from DOM
- Sends to background worker

**background.js** - Manages authentication and API communication
- Handles JWT storage and refresh
- Communicates with backend API
- Implements retry logic and queue management

**popup.js** - Authentication UI and status dashboard
- Login/registration interface
- Real-time stats display
- Queue management

**utils.js** - Shared utilities
- Auth state management (89.85% test coverage)
- Time formatting
- Error handling
- Input validation

---

## 📋 Requirements

### Backend API

Your backend must implement these endpoints:

#### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh

#### Tweet Capture
- `POST /api/tweets/capture` - Receive captured tweets (JWT protected)

#### Health Check (Optional)
- `GET /api/health` - Health check endpoint

See [Feature Specification](#-feature-specification) section below for complete API contract details.

### Browser
- Chrome/Chromium-based browser (Edge, Brave, etc.)
- Manifest V3 support

---

## 🚀 Installation

### Method 1: Load Unpacked (Development)

1. **Clone or download this repository**
   ```bash
   git clone <your-repo-url>
   cd x-search/src/chrome_extension
   ```

2. **Create placeholder icons** (if not included)
   ```bash
   mkdir -p icons
   # Add your icon files or use placeholders (see Quick Start)
   ```

3. **Open Chrome Extensions page**
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode" (toggle in top-right)

4. **Load the extension**
   - Click "Load unpacked"
   - Select the `chrome_extension` folder
   - Extension should now appear in your extensions list

5. **Pin the extension** (optional)
   - Click the puzzle icon in Chrome toolbar
   - Find "X Likes Capture"
   - Click the pin icon to keep it visible

### Method 2: Build and Package (Production)

1. **Create icons**
   - Generate 16x16, 48x48, and 128x128 PNG icons
   - Place in `icons/` folder

2. **Package extension**
   - In Chrome, go to `chrome://extensions/`
   - Click "Pack extension"
   - Select the extension folder
   - This creates a `.crx` file

3. **Distribute**
   - Share the `.crx` file with users
   - Or publish to Chrome Web Store

---

## ⚙️ Configuration

### First-Time Setup

1. **Configure Backend URL**
   - Click the extension icon
   - Go to Settings
   - Enter your backend API URL (e.g., `https://api.yourservice.com`)
   - Click "Test Connection" to verify
   - Save settings

2. **Create Account / Login**
   - Click the extension icon
   - Enter email and password
   - Click "Register" (first time) or "Login"
   - Extension will store JWT tokens securely

3. **Start Capturing**
   - Visit [x.com](https://x.com) or [twitter.com](https://twitter.com)
   - Like any tweet
   - Extension will automatically capture and sync it
   - Check extension popup for status

---

## 🧪 Complete Testing Guide

Step-by-step guide to test the extension locally.

### Part 1: Set Up Test Backend

```bash
cd test_backend
npm install
npm start
```

You should see:
```
🚀 X Likes Capture - Test Backend API
📡 Server running on: http://localhost:3000
```

**Test backend health:**
```bash
curl http://localhost:3000/api/health
```

### Part 2: Load Extension

1. Open `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select `chrome_extension` folder
5. Verify extension appears with no errors

### Part 3: Configure Extension

1. Right-click extension icon → Options
2. Set Backend URL: `http://localhost:3000`
3. Click **Test Connection** → should show ✅
4. Click **Save Settings**

### Part 4: Create Test Account

1. Click extension icon
2. Enter email: `test@example.com`
3. Enter password: `password123`
4. Click **Register**
5. Should show "Logged in as: test@example.com"

Check backend terminal for:
```
📥 POST /api/auth/register
✅ User registered: test@example.com
```

### Part 5: Test Tweet Capture

1. Visit https://x.com or https://twitter.com
2. Like any tweet ❤️
3. Look for brief checkmark ✓ confirmation
4. Click extension icon - should show "Captured: 1 tweets"

Check backend terminal for:
```
📥 POST /api/tweets/capture
📝 Tweet captured:
   User: test@example.com
   Tweet ID: 1234567890123456789
   Author: @someusername
   Text: Tweet content...
```

View captured data:
```bash
curl http://localhost:3000/api/tweets/all
```

### What to Test Next

**Multiple Tweets:**
- Like 5-10 different tweets
- Check stats update in popup
- View all: `http://localhost:3000/api/tweets/all`

**Different Tweet Types:**
- Regular tweets
- Replies
- Retweets
- Quote tweets
- Tweets with images/videos/links

**Offline Queue:**
1. Like a tweet
2. Stop backend (Ctrl+C)
3. Like another tweet
4. Popup should show "Queued: 1"
5. Restart backend: `npm start`
6. Click "Retry Queue"
7. Queued tweet should sync

**Token Refresh:**
1. Like a tweet (works)
2. Logout and login again
3. Like another tweet (should work)

### Debugging Tools

**View all tweets:**
```bash
curl http://localhost:3000/api/tweets/all
```

**Server stats:**
```bash
curl http://localhost:3000/api/stats
```

**Reset all data:**
```bash
curl -X DELETE http://localhost:3000/api/reset
```

**Extension debug mode:**
1. Extension → Settings
2. Enable "Enable debug logging"
3. Press F12 on any page
4. Console shows detailed logs

**View background logs:**
1. Go to `chrome://extensions/`
2. Find "X Likes Capture"
3. Click "service worker" link
4. DevTools opens with background script logs

---

## 📊 Testing Strategy

### Unit Tests (Priority: HIGH)

**Coverage: 65.81%** across tested files
- ✅ utils.js - **89.85% coverage** (69 passing tests)
- ✅ content.js - **52.75% coverage** (24 passing tests)

**Test files:**
- `__tests__/unit/utils.test.js` - All utility functions
- `__tests__/unit/content.test.js` - DOM extraction logic

**Run tests:**
```bash
cd src/chrome_extension
npm test                 # Run all tests
npm run test:coverage    # With coverage report
npm run test:watch       # Watch mode
```

**What we test:**
- Pure functions (formatTimeAgo, isValidEmail, etc.)
- Data extraction (extractTweetData, findTweetArticle)
- Storage operations (getAuthState, saveSettings)
- Error handling (getErrorMessage)

**What we DON'T test:**
- UI/Integration files (background.js, popup.js, options.js)
- These are better tested with E2E tools like Puppeteer
- Excluded from coverage collection for cleaner metrics

### Test Infrastructure

**Tools used:**
- Jest 29.7.0 with jsdom environment
- Babel for ES6+ transpilation
- Manual Chrome API mocks (in `__tests__/setup.js`)
- Test helpers (in `__tests__/helpers.js`)

**Coverage thresholds:**
```javascript
{
  './utils.js': {
    branches: 80%,
    functions: 80%,
    lines: 88%,
    statements: 89%
  },
  './content.js': {
    branches: 40%,
    functions: 40%,
    lines: 50%,
    statements: 50%
  }
}
```

### Future Testing

For comprehensive testing, consider:
- **Integration Tests**: Test Chrome API interactions with jest-chrome
- **E2E Tests**: Use Puppeteer for full user flows
- **Visual Regression**: Snapshot testing for UI components

---

## 📖 Feature Specification

Complete technical specification and API contract.

### Extension Architecture

- **Manifest Version**: V3
- **Target Platform**: Chrome Desktop Browser
- **Target Website**: x.com and twitter.com
- **Primary Language**: JavaScript (ES6+)
- **External Dependency**: Your Backend API (JWT-based)

### Tweet Data Structure

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
  threadId: "1234567890123456789",
  parentTweetId: null,
  conversationId: "1234567890123456789",

  // Media indicators
  hasImage: false,
  hasVideo: false,
  hasLink: false
}
```

### Backend API Contract

#### POST /api/auth/register

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

#### POST /api/auth/login

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

#### POST /api/auth/refresh

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
```

#### POST /api/tweets/capture

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
  "tweetId": "1234567890123456789"
}
```

### Authentication State Management

Stored in `chrome.storage.local` (encrypted by Chrome):

```javascript
{
  auth: {
    accessToken: "eyJhbGciOiJIUzI1NiIs...",  // JWT, 1 hour expiry
    refreshToken: "refresh_abc123...",        // 30 days expiry
    expiresAt: 1700398800000,                 // Unix timestamp
    userId: "user-uuid-here",
    email: "user@example.com"
  },
  settings: {
    backendUrl: "https://api.yourservice.com",
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

### Error Handling

**Authentication Errors:**
- 401 during capture → Try refresh token
- Refresh fails → Clear auth, show login
- Network error during login → Show friendly message

**Network Errors:**
- No internet → Queue locally, show offline status
- Server down → Queue locally, retry later
- Timeout → Retry with exponential backoff

**Rate Limiting:**
- 429 response → Show message, respect Retry-After header
- Queue additional requests

**Storage Errors:**
- Quota exceeded → Warn user, offer to export queue
- Clear old stats to free space

---

## 📊 Usage

### Capturing Tweets

1. **Automatic Capture**
   - Simply like a tweet on X.com
   - Extension detects the like action
   - Extracts tweet metadata
   - Sends to your backend API
   - Shows visual confirmation (checkmark)

2. **Manual Retry**
   - If a tweet fails to sync (offline, error, etc.)
   - It's added to the queue
   - Click "Retry Queue" in popup to manually sync
   - Or wait for automatic retry (every 5 minutes)

### Monitoring Status

**Extension Popup** shows:
- Authentication status
- Today's stats (captured, synced, queued)
- Last capture/sync time
- Queue status

**Settings Page** shows:
- Backend connection status
- Total statistics
- Queue management options

### Advanced Features

**Queue Management**
- **Export Queue**: Settings → Data Management → Export Queue
  - Downloads queued tweets as JSON file
  - Useful for backup or manual processing

- **Clear Queue**: Settings → Data Management → Clear Queue
  - Permanently deletes all queued tweets
  - Cannot be undone

**Debug Mode**
- Settings → Capture Settings → Enable debug logging
- Check browser console for detailed logs
- Useful for troubleshooting

**Auto-Capture Toggle**
- Settings → Capture Settings → Uncheck "Auto-capture likes"
- Extension stops capturing new likes
- Re-enable when ready

---

## 🐛 Troubleshooting

### Extension Not Capturing Tweets

**Check 1: Authentication**
- Click extension icon
- Verify you're logged in
- Try logging out and back in

**Check 2: Auto-Capture Setting**
- Settings → Capture Settings
- Ensure "Auto-capture likes" is enabled

**Check 3: Browser Console**
- Open DevTools (F12)
- Check Console for errors
- Enable debug mode in settings

**Check 4: Extension Permissions**
- Go to `chrome://extensions/`
- Verify "X Likes Capture" has permissions for x.com

### Backend Connection Issues

**Verify Backend URL**
- Settings → Backend Configuration
- Click "Test Connection"
- Should show "Connection successful"

**Check CORS**
- Backend must allow Chrome extension origin
- Check backend CORS configuration

**Check Network**
- Ensure you have internet connection
- Check if backend is running
- Try accessing backend URL in browser

**Test Backend Health:**
```bash
curl http://localhost:3000/api/health
# or your production URL
curl https://api.yourservice.com/api/health
```

### Token Expired Errors

- Extension automatically refreshes tokens
- If refresh fails, you'll be prompted to login
- This is expected after 30 days (refresh token expiry)

### Queue Not Syncing

**Check Authentication**
- Must be logged in to sync queue

**Manual Retry**
- Click "Retry Queue" in popup

**Check Queue Items**
- Settings → Data Management
- View queue size
- Items are retried up to 3 times

### Extension Won't Load

**Missing Icons**
- Make sure icons exist in `icons/` folder
- Create placeholders if needed (see Quick Start)

**Check Errors**
- Go to `chrome://extensions/`
- Look for errors under "X Likes Capture"
- Click "Errors" to see details

**Reload Extension**
- Go to `chrome://extensions/`
- Click reload icon 🔄 under "X Likes Capture"

### Test Backend Issues

**Port Already in Use:**
```bash
# Mac/Linux:
lsof -ti:3000 | xargs kill -9

# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Dependencies Not Installed:**
```bash
cd test_backend
rm -rf node_modules
npm install
npm start
```

---

## 🔒 Security Considerations

### What Gets Stored

**Chrome Storage (Encrypted by Chrome)**
- JWT access token (1 hour expiry)
- Refresh token (30 days expiry)
- User email (for display)
- Backend URL
- Queued tweets (if offline)
- Statistics

### What NEVER Gets Stored

- ❌ Passwords
- ❌ Service account credentials
- ❌ API keys
- ❌ Long-lived tokens
- ❌ Third-party secrets

### Best Practices

1. **Use HTTPS Only**
   - Always use HTTPS for backend API
   - Extension enforces HTTPS

2. **Logout When Done**
   - On shared computers, logout after use
   - Clears all tokens

3. **Keep Extension Updated**
   - Update to latest version
   - Check for security patches

4. **Secure Backend**
   - Implement rate limiting
   - Validate JWT signatures
   - Use short token expiry
   - Enable token revocation

---

## 🛠️ Development

### Local Development

1. **Edit extension code**
2. **Reload extension** in `chrome://extensions/`
3. **Test on X.com**
4. **Check backend logs**
5. **Iterate**

### Testing Code Changes

```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode for development
npm run test:watch
```

### Code Quality Standards

- Modern JavaScript (ES6+, async/await)
- JSDoc comments for public functions
- Comprehensive error handling with try-catch
- Clear user-facing error messages
- No console.log in production (use debug flag)
- Modular code (separate concerns)
- Functions under 50 lines
- Meaningful variable and function names

---

## 📝 License

[Your License Here]

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (run `npm test`)
5. Submit a pull request

---

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Check the troubleshooting section above
- Review this documentation
- Enable debug mode for detailed logs

---

## 🎯 Roadmap

Future enhancements:
- [ ] Bookmark capture (in addition to likes)
- [ ] Manual capture button (capture any tweet)
- [ ] Filter rules (only capture matching criteria)
- [ ] Full thread capture option
- [ ] View capture history in extension
- [ ] Multi-account support
- [ ] Dark mode UI

---

**Built with ❤️ for personal knowledge management**
