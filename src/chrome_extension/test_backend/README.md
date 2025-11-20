# X Likes Capture - Test Backend API

A simple in-memory backend API for testing the X Likes Capture Chrome Extension locally.

## ⚠️ Important Notice

**This is a test/mock backend for development only!**

- Uses in-memory storage (data lost on restart)
- No password hashing
- No database
- No production security measures
- Not suitable for production use

## ✨ Features

- ✅ All required API endpoints
- ✅ JWT authentication
- ✅ Token refresh
- ✅ Tweet capture and storage
- ✅ CORS enabled for extension
- ✅ Console logging for debugging
- ✅ Additional debug endpoints

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd src/test_backend
npm install
```

### 2. Start Server

```bash
npm start
```

Or with auto-reload (using nodemon):

```bash
npm run dev
```

### 3. Configure Extension

1. Open the Chrome extension
2. Go to Settings
3. Set Backend URL to: `http://localhost:3000`
4. Click "Test Connection" - should show ✅ Connected
5. Save settings

### 4. Test the Extension

1. Register a new account in the extension popup
   - Email: `test@example.com`
   - Password: `password123` (min 8 chars)

2. Visit [x.com](https://x.com)

3. Like a tweet

4. Check extension popup - stats should update

5. Check terminal - you'll see the captured tweet data!

## 📡 API Endpoints

### Authentication

**Register User**
```bash
POST http://localhost:3000/api/auth/register
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "password123"
}
```

**Login**
```bash
POST http://localhost:3000/api/auth/login
Content-Type: application/json

{
  "email": "test@example.com",
  "password": "password123"
}
```

**Refresh Token**
```bash
POST http://localhost:3000/api/auth/refresh
Content-Type: application/json

{
  "refreshToken": "refresh_abc123..."
}
```

### Tweet Capture

**Capture Tweet** (requires JWT)
```bash
POST http://localhost:3000/api/tweets/capture
Authorization: Bearer <your-jwt-token>
Content-Type: application/json

{
  "tweetId": "1234567890",
  "tweetUrl": "https://x.com/user/status/1234567890",
  "tweetText": "This is a test tweet",
  "authorUsername": "testuser",
  "authorDisplayName": "Test User",
  ...
}
```

### Debug Endpoints

**Health Check**
```bash
GET http://localhost:3000/api/health
```

**Get User's Tweets** (requires JWT)
```bash
GET http://localhost:3000/api/tweets
Authorization: Bearer <your-jwt-token>
```

**Get All Tweets** (no auth required - debug only)
```bash
GET http://localhost:3000/api/tweets/all
```

**Server Stats**
```bash
GET http://localhost:3000/api/stats
```

**Reset All Data**
```bash
DELETE http://localhost:3000/api/reset
```

## 🧪 Testing Scenarios

### Test 1: Basic Flow
1. Start backend: `npm start`
2. Configure extension with `http://localhost:3000`
3. Register account
4. Like a tweet on X.com
5. Check terminal - should see captured tweet
6. Check extension popup - stats should update

### Test 2: Offline Queue
1. Like a tweet on X.com
2. Stop the backend server (Ctrl+C)
3. Like another tweet
4. Check extension popup - should show "Queued: 1"
5. Restart backend: `npm start`
6. Click "Retry Queue" in extension
7. Check terminal - queued tweet should arrive

### Test 3: Token Refresh
1. Login to extension
2. Wait 1 hour (or manually expire token)
3. Like a tweet
4. Extension should auto-refresh token
5. Tweet should still be captured

### Test 4: Multiple Users
1. Register user1: `test1@example.com`
2. Logout
3. Register user2: `test2@example.com`
4. Like tweets as user2
5. Check `/api/tweets/all` - should see both users' tweets

## 📊 Console Output

The server logs all activity to console:

```
📥 POST /api/auth/register
Body: {
  "email": "test@example.com",
  "password": "password123"
}
✅ User registered: test@example.com
👤 Total users: 1

📥 POST /api/tweets/capture
Body: {...}
📝 Tweet captured:
   User: test@example.com
   Tweet ID: 1234567890
   Author: @elonmusk
   Text: This is a test tweet...
   Total tweets captured: 1
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (optional):

```env
PORT=3000
JWT_SECRET=your-secret-key-here
```

### Default Values

- **Port**: 3000
- **JWT Secret**: `your-secret-key-change-in-production`
- **JWT Expiry**: 1 hour
- **Refresh Token Expiry**: 30 days

## 🐛 Troubleshooting

### Extension can't connect to backend

**Problem**: "Backend: Offline" in extension

**Solutions**:
- Make sure server is running: `npm start`
- Check URL in extension settings: `http://localhost:3000`
- Check terminal for errors
- Make sure nothing else is using port 3000

### CORS errors in browser console

**Problem**: "Access-Control-Allow-Origin" error

**Solution**: The server has CORS enabled for all origins. If you still see errors:
- Restart the backend server
- Clear browser cache
- Reload extension

### Token expired errors

**Problem**: Extension shows "Session expired"

**Solution**:
- This is normal after 1 hour
- Extension should auto-refresh
- If it doesn't, just login again
- Check server console for refresh requests

### Tweets not being captured

**Problem**: No tweets appearing in server logs

**Solutions**:
- Make sure you're logged in to extension
- Check extension popup - should show "Active"
- Enable debug mode in extension settings
- Check browser console (F12) for errors
- Make sure you're on x.com or twitter.com
- Try liking different tweets

## 📝 View Captured Data

### Using curl

```bash
# Get all captured tweets
curl http://localhost:3000/api/tweets/all

# Get server stats
curl http://localhost:3000/api/stats

# Health check
curl http://localhost:3000/api/health
```

### Using Browser

Simply visit in your browser:
- http://localhost:3000/api/health
- http://localhost:3000/api/stats
- http://localhost:3000/api/tweets/all

### Using Browser DevTools

1. Open extension popup
2. Right-click → Inspect
3. Go to Console tab
4. Enable debug mode in settings
5. Like a tweet
6. See detailed logs

## 🔄 Resetting Data

### Reset everything:
```bash
curl -X DELETE http://localhost:3000/api/reset
```

Or restart the server (data is in-memory).

## 📦 What Gets Stored

### Users
```javascript
{
  userId: "user_1234567890_abc123",
  email: "test@example.com",
  password: "password123", // NOT hashed in test backend!
  createdAt: "2024-11-19T10:30:00.000Z"
}
```

### Captured Tweets
```javascript
{
  // Extension data
  tweetId: "1234567890",
  tweetUrl: "https://x.com/user/status/1234567890",
  tweetText: "Tweet content...",
  authorUsername: "username",
  authorDisplayName: "Display Name",
  // ... all other fields from extension

  // Server-added metadata
  userId: "user_1234567890_abc123",
  userEmail: "test@example.com",
  receivedAt: "2024-11-19T10:35:00.000Z",
  messageId: "msg_1234567890_xyz789"
}
```

## 🚀 Next Steps

After testing with this backend:

1. **Build a real backend** with:
   - Proper database (PostgreSQL, MongoDB, etc.)
   - Password hashing (bcrypt)
   - Token revocation
   - Rate limiting
   - Pub/Sub integration (if needed)

2. **Or use existing services**:
   - Firebase Authentication
   - Auth0
   - Supabase
   - AWS Cognito

3. **Deploy**:
   - Host on Vercel, Railway, Render, etc.
   - Use environment variables
   - Enable HTTPS
   - Set up monitoring

## 📚 Resources

- [Express.js Documentation](https://expressjs.com/)
- [JWT Documentation](https://jwt.io/)
- [Extension Feature Spec](../chrome_extension/FEATURE_SPEC.md)

---

Happy testing! 🎉
