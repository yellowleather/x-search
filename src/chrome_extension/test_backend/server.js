/**
 * Test/Mock Backend API for X Likes Capture Chrome Extension
 * This is a simple in-memory backend for testing the extension
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';
const JWT_EXPIRY = '1h'; // 1 hour
const REFRESH_TOKEN_EXPIRY = '30d'; // 30 days

// Middleware
app.use(cors()); // Allow all origins for testing
app.use(express.json());

// In-memory storage (for testing only)
const users = new Map(); // email -> user object
const refreshTokens = new Map(); // refreshToken -> userId
const capturedTweets = []; // Array of captured tweets

// Logging middleware
app.use((req, res, next) => {
  console.log(`\n📥 ${req.method} ${req.path}`);
  if (req.body && Object.keys(req.body).length > 0) {
    console.log('Body:', JSON.stringify(req.body, null, 2));
  }
  next();
});

// ============================================================================
// AUTHENTICATION ENDPOINTS
// ============================================================================

/**
 * POST /api/auth/register
 * Register a new user
 */
app.post('/api/auth/register', (req, res) => {
  const { email, password } = req.body;

  // Validate input
  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password required' });
  }

  if (password.length < 8) {
    return res.status(400).json({ error: 'Password must be at least 8 characters' });
  }

  // Check if user already exists
  if (users.has(email)) {
    return res.status(409).json({ error: 'User already exists' });
  }

  // Create user
  const userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const user = {
    userId,
    email,
    password, // In production, hash this!
    createdAt: new Date().toISOString()
  };

  users.set(email, user);

  // Generate tokens
  const accessToken = jwt.sign({ userId, email }, JWT_SECRET, { expiresIn: JWT_EXPIRY });
  const refreshToken = `refresh_${Math.random().toString(36).substr(2, 32)}`;

  // Store refresh token
  refreshTokens.set(refreshToken, userId);

  console.log('✅ User registered:', email);
  console.log('👤 Total users:', users.size);

  res.status(201).json({
    accessToken,
    refreshToken,
    expiresIn: 3600, // 1 hour in seconds
    userId
  });
});

/**
 * POST /api/auth/login
 * Login existing user
 */
app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;

  // Validate input
  if (!email || !password) {
    return res.status(400).json({ error: 'Email and password required' });
  }

  // Check if user exists
  const user = users.get(email);
  if (!user) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Check password (in production, use bcrypt.compare)
  if (user.password !== password) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Generate tokens
  const accessToken = jwt.sign(
    { userId: user.userId, email: user.email },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRY }
  );
  const refreshToken = `refresh_${Math.random().toString(36).substr(2, 32)}`;

  // Store refresh token
  refreshTokens.set(refreshToken, user.userId);

  console.log('✅ User logged in:', email);

  res.json({
    accessToken,
    refreshToken,
    expiresIn: 3600, // 1 hour in seconds
    userId: user.userId
  });
});

/**
 * POST /api/auth/refresh
 * Refresh access token
 */
app.post('/api/auth/refresh', (req, res) => {
  const { refreshToken } = req.body;

  // Validate input
  if (!refreshToken) {
    return res.status(400).json({ error: 'Refresh token required' });
  }

  // Check if refresh token exists
  const userId = refreshTokens.get(refreshToken);
  if (!userId) {
    return res.status(401).json({ error: 'Invalid refresh token' });
  }

  // Find user by userId
  const user = Array.from(users.values()).find(u => u.userId === userId);
  if (!user) {
    return res.status(401).json({ error: 'User not found' });
  }

  // Generate new access token
  const accessToken = jwt.sign(
    { userId: user.userId, email: user.email },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRY }
  );

  console.log('✅ Token refreshed for:', user.email);

  res.json({
    accessToken,
    expiresIn: 3600
  });
});

// ============================================================================
// JWT VERIFICATION MIDDLEWARE
// ============================================================================

function verifyToken(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'No token provided' });
  }

  const token = authHeader.substring(7); // Remove 'Bearer ' prefix

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded; // Add user info to request
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token expired' });
    }
    return res.status(401).json({ error: 'Invalid token' });
  }
}

// ============================================================================
// TWEET CAPTURE ENDPOINT
// ============================================================================

/**
 * POST /api/tweets/capture
 * Capture a liked tweet (protected endpoint)
 */
app.post('/api/tweets/capture', verifyToken, (req, res) => {
  const tweetData = req.body;
  const { userId, email } = req.user;

  // Validate tweet data
  if (!tweetData.tweetId) {
    return res.status(400).json({ error: 'Tweet ID required' });
  }

  // Store tweet with metadata
  const capturedTweet = {
    ...tweetData,
    userId,
    userEmail: email,
    receivedAt: new Date().toISOString(),
    messageId: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  };

  capturedTweets.push(capturedTweet);

  // Log captured tweet
  console.log('📝 Tweet captured:');
  console.log(`   User: ${email}`);
  console.log(`   Tweet ID: ${tweetData.tweetId}`);
  console.log(`   Author: @${tweetData.authorUsername}`);
  console.log(`   Text Length: ${tweetData.tweetText?.length || 0} characters`);
  console.log(`   Text Preview: ${tweetData.tweetText?.substring(0, 100)}${tweetData.tweetText?.length > 100 ? '...' : ''}`);
  console.log(`   Full Text: ${tweetData.tweetText}`);
  console.log(`   Total tweets captured: ${capturedTweets.length}`);

  res.json({
    status: 'queued',
    tweetId: tweetData.tweetId,
    messageId: capturedTweet.messageId
  });
});

// ============================================================================
// ADDITIONAL ENDPOINTS FOR TESTING/DEBUG
// ============================================================================

/**
 * GET /api/health
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    version: '1.0.0',
    timestamp: new Date().toISOString()
  });
});

/**
 * GET /api/tweets
 * Get all captured tweets (for testing/debugging)
 */
app.get('/api/tweets', verifyToken, (req, res) => {
  const { userId } = req.user;

  // Filter tweets for this user
  const userTweets = capturedTweets.filter(t => t.userId === userId);

  res.json({
    total: userTweets.length,
    tweets: userTweets
  });
});

/**
 * GET /api/tweets/all
 * Get all captured tweets from all users (admin/debug)
 */
app.get('/api/tweets/all', (req, res) => {
  res.json({
    total: capturedTweets.length,
    tweets: capturedTweets.map(t => ({
      tweetId: t.tweetId,
      author: t.authorUsername,
      text: t.tweetText?.substring(0, 100),
      user: t.userEmail,
      capturedAt: t.capturedAt,
      receivedAt: t.receivedAt
    }))
  });
});

/**
 * GET /api/stats
 * Get server statistics (admin/debug)
 */
app.get('/api/stats', (req, res) => {
  res.json({
    users: users.size,
    tweets: capturedTweets.length,
    refreshTokens: refreshTokens.size,
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

/**
 * DELETE /api/reset
 * Reset all data (for testing only!)
 */
app.delete('/api/reset', (req, res) => {
  users.clear();
  refreshTokens.clear();
  capturedTweets.length = 0;

  console.log('🔄 All data reset!');

  res.json({
    message: 'All data cleared',
    timestamp: new Date().toISOString()
  });
});

// ============================================================================
// ERROR HANDLING
// ============================================================================

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error('❌ Error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ============================================================================
// START SERVER
// ============================================================================

app.listen(PORT, () => {
  console.log('\n' + '='.repeat(60));
  console.log('🚀 X Likes Capture - Test Backend API');
  console.log('='.repeat(60));
  console.log(`\n📡 Server running on: http://localhost:${PORT}`);
  console.log(`🔐 JWT Secret: ${JWT_SECRET.substring(0, 10)}...`);
  console.log(`\n📚 Available Endpoints:`);
  console.log(`   POST   /api/auth/register    - Register new user`);
  console.log(`   POST   /api/auth/login       - Login user`);
  console.log(`   POST   /api/auth/refresh     - Refresh token`);
  console.log(`   POST   /api/tweets/capture   - Capture tweet (protected)`);
  console.log(`   GET    /api/health           - Health check`);
  console.log(`   GET    /api/tweets           - Get user's tweets (protected)`);
  console.log(`   GET    /api/tweets/all       - Get all tweets (debug)`);
  console.log(`   GET    /api/stats            - Server stats`);
  console.log(`   DELETE /api/reset            - Reset all data`);
  console.log(`\n💡 Use in extension: http://localhost:${PORT}`);
  console.log(`\n` + '='.repeat(60) + '\n');
});
