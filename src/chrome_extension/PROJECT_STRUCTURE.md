# X Likes Capture - Project Structure

Complete directory structure for the Chrome extension and test backend.

## 📁 Directory Structure

```
src/chrome_extension/
├── 📄 Core Extension Files
│   ├── manifest.json           # Extension manifest (V3)
│   ├── content.js             # DOM monitoring & tweet capture
│   ├── background.js          # Service worker (auth & API)
│   ├── utils.js               # Shared utilities
│   └── debug-capture.js       # Debug script for testing
│
├── 🎨 UI Files
│   ├── popup.html             # Popup interface
│   ├── popup.js               # Popup logic
│   ├── popup.css              # Popup styles
│   ├── options.html           # Settings page
│   └── options.js             # Settings logic
│
├── 🖼️ Icons
│   └── icons/
│       ├── README.md          # Icon creation guide
│       ├── icon16.png         # 16x16 toolbar icon
│       ├── icon48.png         # 48x48 management icon
│       └── icon128.png        # 128x128 store icon
│
├── 📚 Documentation
│   ├── README.md              # Main documentation
│   ├── QUICKSTART.md          # Quick start guide
│   ├── TESTING_GUIDE.md       # Complete testing guide
│   ├── FEATURE_SPEC.md        # Full specification
│   └── PROJECT_STRUCTURE.md   # This file
│
└── 🧪 Test Backend
    └── test_backend/
        ├── server.js          # Mock backend API
        ├── package.json       # Backend dependencies
        ├── .env.example       # Environment config example
        ├── .gitignore         # Git ignore rules
        └── README.md          # Backend documentation
```

## 🚀 Quick Navigation

### For Users

- **Installation**: Start with [QUICKSTART.md](QUICKSTART.md)
- **Complete Guide**: See [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **Full Documentation**: Read [README.md](README.md)

### For Developers

- **Architecture**: See [FEATURE_SPEC.md](FEATURE_SPEC.md)
- **Test Backend**: Check [test_backend/README.md](test_backend/README.md)
- **Code Structure**: Review this file

## 📦 File Descriptions

### Extension Core

| File | Purpose | Lines |
|------|---------|-------|
| `manifest.json` | Extension configuration, permissions, content scripts | ~50 |
| `content.js` | Monitors X.com DOM, captures tweets when liked | ~365 |
| `background.js` | Handles auth, API communication, queue management | ~300 |
| `utils.js` | Shared functions (auth, time formatting, errors) | ~200 |

### UI Components

| File | Purpose | Lines |
|------|---------|-------|
| `popup.html` | Main popup UI with login/stats views | ~80 |
| `popup.js` | Popup logic, authentication flow, stats display | ~350 |
| `popup.css` | Modern, clean styling for popup | ~200 |
| `options.html` | Settings page with backend config | ~120 |
| `options.js` | Settings logic, connection testing | ~250 |

### Test Backend

| File | Purpose | Lines |
|------|---------|-------|
| `server.js` | Express API with JWT auth & tweet capture | ~350 |
| `package.json` | Dependencies (express, cors, jsonwebtoken) | ~25 |
| `README.md` | Backend setup and testing guide | ~400 |

## 🔄 Workflow

### Development Flow
```
1. Edit extension code
2. Reload extension in chrome://extensions/
3. Test on X.com
4. Check backend logs
5. Iterate
```

### Testing Flow
```
1. Start test backend (npm start)
2. Configure extension
3. Register/login
4. Like tweets on X.com
5. Verify capture in backend logs
```

## 🎯 Key Features

### Extension Features
- ✅ JWT-based authentication
- ✅ Automatic tweet capture on like
- ✅ Offline queue with retry
- ✅ Token refresh handling
- ✅ Visual capture confirmation
- ✅ Real-time statistics
- ✅ Settings management

### Test Backend Features
- ✅ Full authentication API
- ✅ Tweet capture endpoint
- ✅ In-memory storage
- ✅ Console logging
- ✅ Debug endpoints
- ✅ CORS enabled

## 📊 Data Flow

```
User likes tweet on X.com
         ↓
content.js captures tweet metadata
         ↓
Sends to background.js via message
         ↓
background.js checks authentication
         ↓
Sends to backend API with JWT
         ↓
Backend stores & logs tweet
         ↓
Extension shows success indicator
```

## 🔧 Configuration Files

### Extension Config
- `manifest.json` - Chrome extension manifest
- No environment variables needed

### Backend Config
- `.env` (optional) - Port, JWT secret
- Defaults: Port 3000, in-memory storage

## 📝 Important Notes

### Security
- Extension stores only JWT tokens (1h expiry)
- No API keys or secrets in extension
- Test backend is NOT for production

### Browser Compatibility
- Chrome/Chromium browsers
- Manifest V3 required
- ES6+ JavaScript

### Backend
- Node.js required (v14+)
- In-memory storage (data lost on restart)
- No database needed for testing

## 🚢 Deployment

### Extension
1. Create proper icons (replace placeholders)
2. Test thoroughly
3. Package extension (.zip or .crx)
4. Publish to Chrome Web Store (optional)

### Backend
1. Build production backend with:
   - Database (PostgreSQL, MongoDB)
   - Password hashing (bcrypt)
   - Rate limiting
   - Proper auth flow
2. Deploy to hosting service
3. Update extension backend URL

## 🆘 Quick Links

- [Chrome Extensions Docs](https://developer.chrome.com/docs/extensions/)
- [Manifest V3 Migration](https://developer.chrome.com/docs/extensions/mv3/intro/)
- [JWT Documentation](https://jwt.io/)
- [Express.js Guide](https://expressjs.com/)

---

**Last Updated**: 2024-11-19
