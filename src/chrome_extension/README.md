# X Likes Capture Chrome Extension

A secure Chrome extension that automatically captures tweets when you like them on X.com (Twitter) and sends them to your backend API for personal knowledge management.

## 🔐 Security Architecture

This extension follows a **zero-trust architecture**:
- ✅ Stores only short-lived JWT tokens (1 hour expiry)
- ✅ No service account credentials
- ✅ No API keys
- ✅ All sensitive operations happen server-side
- ✅ Tokens stored in encrypted Chrome storage
- ✅ HTTPS-only communication

## ✨ Features

- **Automatic Capture**: Captures tweet metadata when you like a tweet
- **Secure Authentication**: JWT-based authentication with token refresh
- **Offline Support**: Queues tweets locally when offline, syncs when back online
- **Real-time Stats**: Track captured, synced, and queued tweets
- **Manual Retry**: Retry failed captures with one click
- **Configurable Backend**: Point to your own backend API
- **Privacy-First**: Only captures metadata, no tracking or analytics

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

See [FEATURE_SPEC.md](FEATURE_SPEC.md) for complete API contract details.

### Browser
- Chrome/Chromium-based browser (Edge, Brave, etc.)
- Manifest V3 support

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
   # Add your icon files: icon16.png, icon48.png, icon128.png
   # Or use placeholder images for testing
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

### Captured Data

Each captured tweet includes:
- Tweet ID and URL
- Tweet text content
- Author username and display name
- Timestamp (when posted)
- Capture timestamp
- Context flags (reply, retweet, quote, thread)
- Media indicators (image, video, link)

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

## 🔧 Advanced Features

### Queue Management

**Export Queue**
- Settings → Data Management → Export Queue
- Downloads queued tweets as JSON file
- Useful for backup or manual processing

**Clear Queue**
- Settings → Data Management → Clear Queue
- Permanently deletes all queued tweets
- Cannot be undone

### Debug Mode

Enable debug logging:
- Settings → Capture Settings → Enable debug logging
- Check browser console for detailed logs
- Useful for troubleshooting

### Auto-Capture Toggle

Temporarily disable capture:
- Settings → Capture Settings → Uncheck "Auto-capture likes"
- Extension stops capturing new likes
- Re-enable when ready

## 🛠️ Development

### Project Structure

```
chrome_extension/
├── manifest.json          # Extension manifest (V3)
├── background.js          # Service worker (auth, API communication)
├── content.js            # DOM monitoring and capture
├── popup.html            # Popup UI
├── popup.js              # Popup logic
├── popup.css             # Popup styles
├── options.html          # Settings page
├── options.js            # Settings logic
├── utils.js              # Shared utilities
├── icons/                # Extension icons
│   ├── icon16.png
│   ├── icon48.png
│   └── icon128.png
├── README.md             # This file
└── FEATURE_SPEC.md       # Full specification
```

### Key Components

**content.js**
- Monitors X.com DOM for like actions
- Extracts tweet metadata
- Sends to background worker

**background.js**
- Manages authentication state
- Handles API communication
- Implements retry logic
- Manages local queue

**popup.js**
- Login/registration UI
- Real-time stats display
- Queue management

**utils.js**
- Auth state management
- Time formatting
- Error handling
- Common utilities

### Testing

1. **Manual Testing**
   ```bash
   # Load extension in Chrome
   # Visit x.com
   # Test various scenarios:
   - Like a regular tweet
   - Like a reply
   - Like a retweet
   - Like with network offline
   - Unlike handling
   ```

2. **Backend Testing**
   - Test all API endpoints
   - Verify JWT validation
   - Test rate limiting
   - Test error responses

3. **Edge Cases**
   - Rapid liking (10+ tweets quickly)
   - Very long tweet text
   - Special characters
   - X UI changes

## 🐛 Troubleshooting

### Extension Not Capturing Tweets

1. **Check Authentication**
   - Click extension icon
   - Verify you're logged in
   - Try logging out and back in

2. **Check Auto-Capture Setting**
   - Settings → Capture Settings
   - Ensure "Auto-capture likes" is enabled

3. **Check Browser Console**
   - Open DevTools (F12)
   - Check Console for errors
   - Enable debug mode in settings

### Backend Connection Issues

1. **Verify Backend URL**
   - Settings → Backend Configuration
   - Click "Test Connection"
   - Should show "Connection successful"

2. **Check CORS**
   - Backend must allow Chrome extension origin
   - Check backend CORS configuration

3. **Check Network**
   - Ensure you have internet connection
   - Check if backend is running
   - Try accessing backend URL in browser

### Token Expired Errors

- Extension automatically refreshes tokens
- If refresh fails, you'll be prompted to login
- This is expected after 30 days (refresh token expiry)

### Queue Not Syncing

1. **Check Authentication**
   - Must be logged in to sync queue

2. **Manual Retry**
   - Click "Retry Queue" in popup

3. **Check Queue Items**
   - Settings → Data Management
   - View queue size
   - Items are retried up to 3 times

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

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review [FEATURE_SPEC.md](FEATURE_SPEC.md) for technical details

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
