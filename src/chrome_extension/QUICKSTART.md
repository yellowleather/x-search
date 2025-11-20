# Quick Start Guide

Get up and running with X Likes Capture in 5 minutes!

## Prerequisites

- [ ] Chrome or Chromium-based browser
- [ ] Backend API running (see backend requirements below)
- [ ] Extension icons created (see icons/README.md)

## Step 1: Prepare Icons

Create placeholder icons for testing:

```bash
cd src/chrome_extension/icons

# Download placeholders (using curl)
curl "https://via.placeholder.com/16/1d9bf0/FFFFFF?text=X" -o icon16.png
curl "https://via.placeholder.com/48/1d9bf0/FFFFFF?text=X" -o icon48.png
curl "https://via.placeholder.com/128/1d9bf0/FFFFFF?text=X" -o icon128.png
```

Or see [icons/README.md](icons/README.md) for other methods.

## Step 2: Load Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `chrome_extension` folder
5. Extension appears in your extensions list ✅

## Step 3: Configure Backend

1. Click the extension icon in Chrome toolbar
2. Click **Settings** (or right-click icon → Options)
3. Enter your backend URL (e.g., `https://api.yourservice.com`)
4. Click **Test Connection** to verify
5. Click **Save Settings**

## Step 4: Authenticate

1. Click the extension icon
2. Enter your email and password
3. Click **Register** (first time) or **Login**
4. You should see the authenticated view with stats ✅

## Step 5: Test Capture

1. Visit [x.com](https://x.com) or [twitter.com](https://twitter.com)
2. Find a tweet you like
3. Click the **like** button ❤️
4. You should see a small checkmark appear briefly ✓
5. Click the extension icon to see stats updated

## Troubleshooting Quick Fixes

### Extension won't load
- **Missing icons**: Create placeholder icons (Step 1)
- **Wrong folder**: Make sure you select the `chrome_extension` folder, not the parent folder

### Backend connection fails
- **URL typo**: Double-check the backend URL
- **Not running**: Make sure your backend API is running
- **CORS issue**: Backend must allow requests from Chrome extension

### Not capturing tweets
- **Not logged in**: Click extension icon, make sure you're authenticated
- **Auto-capture disabled**: Settings → Enable "Auto-capture likes"
- **Wrong site**: Make sure you're on x.com or twitter.com

### Check console for errors
1. Open DevTools (F12)
2. Go to **Console** tab
3. Look for errors from `[X Likes Capture]`
4. Enable debug mode in Settings for more details

## Backend API Requirements

Your backend must implement these endpoints:

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Token refresh

### Tweet Capture
- `POST /api/tweets/capture` - Receive captured tweets

### Optional
- `GET /api/health` - Health check

See [FEATURE_SPEC.md](FEATURE_SPEC.md) for complete API specifications.

## Example Backend Response

**Login Success** (`POST /api/auth/login`):
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "refresh_abc123...",
  "expiresIn": 3600,
  "userId": "user-uuid-here"
}
```

**Capture Success** (`POST /api/tweets/capture`):
```json
{
  "status": "queued",
  "tweetId": "1234567890123456789",
  "messageId": "pubsub-message-id"
}
```

## Next Steps

- ✅ Extension loaded and running
- ✅ Backend connected
- ✅ First tweet captured

Now you can:
- View stats in the extension popup
- Configure advanced settings
- Export queued tweets
- Monitor capture history

## Need Help?

- Check [README.md](README.md) for full documentation
- Review [FEATURE_SPEC.md](FEATURE_SPEC.md) for technical details
- Open an issue on GitHub
- Enable debug mode for detailed logs

---

Happy capturing! 🚀
