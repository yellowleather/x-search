# Complete Testing Guide - X Likes Capture Extension

Step-by-step guide to test the extension locally without a production backend.

## 🎯 Overview

You'll set up:
1. ✅ Test backend API (Node.js/Express)
2. ✅ Chrome extension with placeholder icons
3. ✅ Test user account
4. ✅ Tweet capture testing on X.com

**Total time**: ~10 minutes

---

## 📋 Prerequisites

- [x] Node.js installed (v14 or higher)
- [x] Chrome browser
- [x] Extension files already created
- [x] Active X.com (Twitter) account

---

## Part 1: Set Up Test Backend (5 minutes)

### Step 1: Install Backend Dependencies

```bash
cd src/chrome_extension/test_backend
npm install
```

This installs: `express`, `cors`, `jsonwebtoken`, `dotenv`

### Step 2: Start the Backend Server

```bash
npm start
```

You should see:
```
🚀 X Likes Capture - Test Backend API
📡 Server running on: http://localhost:3000
```

**Keep this terminal open!** The server needs to stay running.

### Step 3: Test Backend Health

Open a new terminal and run:
```bash
curl http://localhost:3000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "..."
}
```

✅ Backend is ready!

---

## Part 2: Create Placeholder Icons (2 minutes)

The extension needs icon files to load. Create simple placeholders:

### Option A: Download Placeholders (Easiest)

```bash
cd src/chrome_extension/icons

# Download placeholder icons
curl "https://via.placeholder.com/16/1d9bf0/FFFFFF?text=X" -o icon16.png
curl "https://via.placeholder.com/48/1d9bf0/FFFFFF?text=X" -o icon48.png
curl "https://via.placeholder.com/128/1d9bf0/FFFFFF?text=X" -o icon128.png
```

### Option B: Copy Any PNG Files

If you have any PNG images:
```bash
cd src/chrome_extension/icons

# Copy and rename any PNG file
cp /path/to/any-image.png icon16.png
cp /path/to/any-image.png icon48.png
cp /path/to/any-image.png icon128.png
```

### Option C: Use ImageMagick (if installed)

```bash
cd src/chrome_extension/icons

convert -size 16x16 xc:#1d9bf0 icon16.png
convert -size 48x48 xc:#1d9bf0 icon48.png
convert -size 128x128 xc:#1d9bf0 icon128.png
```

✅ Icons ready!

---

## Part 3: Load Extension in Chrome (2 minutes)

### Step 1: Open Extensions Page

1. Open Chrome
2. Navigate to: `chrome://extensions/`
3. Enable **Developer mode** (toggle in top-right)

### Step 2: Load the Extension

1. Click **Load unpacked**
2. Navigate to and select: `x-search/src/chrome_extension/`
3. Click **Select**

### Step 3: Verify Extension Loaded

You should see:
- ✅ "X Likes Capture" in your extensions list
- ✅ Version 1.0.0
- ✅ No errors

### Step 4: Pin the Extension (Optional)

1. Click the puzzle icon 🧩 in Chrome toolbar
2. Find "X Likes Capture"
3. Click the pin 📌 icon

✅ Extension installed!

---

## Part 4: Configure Extension (1 minute)

### Step 1: Open Extension Settings

**Method A**: Right-click extension icon → Options
**Method B**: Click extension icon → Settings button

### Step 2: Set Backend URL

1. In "Backend API Configuration" section
2. Set API URL to: `http://localhost:3000`
3. Click **Test Connection**
4. Should show: ✅ "Connection successful!"
5. Click **Save Settings**

✅ Extension configured!

---

## Part 5: Create Test Account (1 minute)

### Step 1: Open Extension Popup

Click the extension icon in Chrome toolbar

### Step 2: Register

1. Enter email: `test@example.com`
2. Enter password: `password123` (min 8 chars)
3. Click **Register**

You should see:
- ✅ "Logged in as: test@example.com"
- ✅ "Status: ✅ Active"
- ✅ Stats showing "Captured: 0 tweets"

### Check Backend Terminal

You should see in the backend terminal:
```
📥 POST /api/auth/register
✅ User registered: test@example.com
👤 Total users: 1
```

✅ Account created!

---

## Part 6: Test Tweet Capture (Final Test!)

### Step 1: Visit X.com

1. Open a new tab
2. Go to: https://x.com or https://twitter.com
3. Log in to your X/Twitter account (if not already)

### Step 2: Like a Tweet

1. Scroll through your timeline
2. Find any tweet
3. Click the **heart/like** button ❤️

### Step 3: Visual Confirmation

You should see:
- ✅ A small checkmark (✓) appears briefly next to the heart icon

### Step 4: Check Extension Popup

1. Click the extension icon
2. You should see:
   - "Captured: 1 tweets"
   - "Synced: 1 tweets"
   - "Last capture: Just now"

### Step 5: Check Backend Terminal

In your backend terminal, you should see:
```
📥 POST /api/tweets/capture
📝 Tweet captured:
   User: test@example.com
   Tweet ID: 1234567890123456789
   Author: @someusername
   Text: Tweet content here...
   Total tweets captured: 1
```

### Step 6: View Captured Data

Open in browser: http://localhost:3000/api/tweets/all

You should see JSON with your captured tweet!

✅ **SUCCESS!** Extension is working!

---

## 🎉 What to Test Next

### Test Multiple Tweets
1. Like 5-10 different tweets
2. Check extension popup - stats should update
3. Check backend terminal - should log each capture
4. View all: http://localhost:3000/api/tweets/all

### Test Different Tweet Types
- Regular tweets
- Replies (tweets that are responses)
- Retweets
- Quote tweets
- Tweets with images
- Tweets with videos
- Tweets with links

### Test Offline Queue
1. Like a tweet
2. Stop backend (Ctrl+C in terminal)
3. Like another tweet
4. Extension popup should show "Queued: 1"
5. Restart backend: `npm start`
6. Click "Retry Queue" in popup
7. Queued tweet should sync

### Test Token Refresh
For quick testing, you can:
1. Like a tweet (works)
2. Logout and login again
3. Like another tweet (should work)

---

## 🐛 Troubleshooting

### Extension not capturing tweets

**Check 1**: Are you logged in?
- Click extension icon
- Should show "Logged in as: ..."
- If not, register/login again

**Check 2**: Is auto-capture enabled?
- Extension → Settings
- "Auto-capture likes" should be checked

**Check 3**: Is backend running?
- Check terminal running `npm start`
- Visit: http://localhost:3000/api/health
- Should return `{"status":"healthy"}`

**Check 4**: Check browser console
- Press F12 on X.com
- Go to Console tab
- Look for errors from `[X Likes Capture]`

### Backend connection fails

**Check 1**: Is server running?
```bash
# From chrome_extension/test_backend directory
cd src/chrome_extension/test_backend
npm start
```

**Check 2**: Correct URL in extension?
- Settings → Backend URL should be `http://localhost:3000`

**Check 3**: Port already in use?
```bash
# Stop any process on port 3000
# On Mac/Linux:
lsof -ti:3000 | xargs kill -9

# On Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Extension won't load

**Missing icons**: Make sure you created icon files (Part 2)

**Check errors**:
- Go to `chrome://extensions/`
- Look for errors under "X Likes Capture"
- Click "Errors" to see details

**Reload extension**:
- Go to `chrome://extensions/`
- Click reload icon 🔄 under "X Likes Capture"

---

## 📊 Debugging Tools

### Backend API Endpoints

**View all tweets**:
```bash
curl http://localhost:3000/api/tweets/all
```

**Server stats**:
```bash
curl http://localhost:3000/api/stats
```

**Reset all data**:
```bash
curl -X DELETE http://localhost:3000/api/reset
```

### Extension Debug Mode

1. Extension → Settings
2. Enable "Enable debug logging"
3. Press F12 on any page
4. Console will show detailed logs

### View Extension Background Logs

1. Go to `chrome://extensions/`
2. Find "X Likes Capture"
3. Click "service worker" link
4. DevTools opens showing background script logs

---

## ✅ Success Checklist

After testing, you should have:

- [x] Backend running on http://localhost:3000
- [x] Extension loaded in Chrome
- [x] Test account registered
- [x] At least one tweet captured
- [x] Stats showing in extension popup
- [x] Tweet data visible in backend terminal
- [x] Data accessible via http://localhost:3000/api/tweets/all

---

## 🚀 Next Steps

### For Development
- Modify extension code
- Test new features
- Debug issues
- View captured data structure

### For Production
You'll need to:
1. Build a real backend with:
   - Database (PostgreSQL, MongoDB, etc.)
   - Password hashing
   - Proper authentication
   - Rate limiting
   - Pub/Sub integration (optional)

2. Deploy backend to:
   - Vercel, Railway, Render, Fly.io
   - AWS, Google Cloud, Azure
   - Any Node.js hosting

3. Update extension:
   - Point to production backend URL
   - Create proper icons
   - Package extension
   - (Optional) Publish to Chrome Web Store

---

## 📚 Additional Resources

- [Extension README](README.md)
- [Test Backend README](test_backend/README.md)
- [Feature Spec](FEATURE_SPEC.md)
- [Quick Start Guide](QUICKSTART.md)

---

**Happy testing! 🎉**

If you encounter issues, check the troubleshooting section or create an issue.
