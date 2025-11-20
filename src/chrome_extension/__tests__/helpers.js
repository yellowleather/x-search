/**
 * Test Helpers and Utilities
 * Shared functions for creating test data and mocks
 */

/**
 * Create a mock tweet article DOM element
 */
function createMockTweetArticle(options = {}) {
  const {
    tweetId = '1234567890123456789',
    tweetText = 'This is a test tweet',
    authorUsername = 'testuser',
    authorDisplayName = 'Test User',
    timestamp = '2024-11-19T10:30:00.000Z',
    isReply = false,
    hasImage = false,
    hasVideo = false
  } = options;

  const article = document.createElement('article');
  article.setAttribute('data-testid', 'tweet');

  // Add time element with link
  const time = document.createElement('time');
  time.setAttribute('datetime', timestamp);
  const link = document.createElement('a');
  link.href = `https://x.com/${authorUsername}/status/${tweetId}`;
  link.appendChild(time);
  article.appendChild(link);

  // Add tweet text
  const tweetTextDiv = document.createElement('div');
  tweetTextDiv.setAttribute('data-testid', 'tweetText');
  tweetTextDiv.textContent = tweetText;
  article.appendChild(tweetTextDiv);

  // Add author info
  const userNameDiv = document.createElement('div');
  userNameDiv.setAttribute('data-testid', 'User-Name');

  const displayNameLink = document.createElement('a');
  displayNameLink.textContent = authorDisplayName;
  userNameDiv.appendChild(displayNameLink);

  const usernameLink = document.createElement('a');
  usernameLink.textContent = `@${authorUsername}`;
  userNameDiv.appendChild(usernameLink);

  article.appendChild(userNameDiv);

  // Add reply indicator if needed
  if (isReply) {
    const replyDiv = document.createElement('div');
    replyDiv.setAttribute('data-testid', 'reply');
    article.appendChild(replyDiv);
  }

  // Add media indicators
  if (hasImage) {
    const imageDiv = document.createElement('div');
    imageDiv.setAttribute('data-testid', 'tweetPhoto');
    article.appendChild(imageDiv);
  }

  if (hasVideo) {
    const videoDiv = document.createElement('div');
    videoDiv.setAttribute('data-testid', 'videoPlayer');
    article.appendChild(videoDiv);
  }

  return article;
}

/**
 * Create a mock like button element
 */
function createMockLikeButton(liked = false) {
  const button = document.createElement('button');
  button.setAttribute('data-testid', liked ? 'unlike' : 'like');
  return button;
}

/**
 * Create mock auth state
 */
function createMockAuthState(options = {}) {
  const {
    accessToken = 'mock_access_token',
    refreshToken = 'mock_refresh_token',
    expiresAt = Date.now() + 3600000, // 1 hour from now
    userId = 'user_123',
    email = 'test@example.com'
  } = options;

  return {
    accessToken,
    refreshToken,
    expiresAt,
    userId,
    email
  };
}

/**
 * Create mock tweet data
 */
function createMockTweetData(options = {}) {
  const {
    tweetId = '1234567890123456789',
    tweetUrl = 'https://x.com/testuser/status/1234567890123456789',
    tweetText = 'This is a test tweet',
    authorUsername = 'testuser',
    authorDisplayName = 'Test User',
    timestamp = '2024-11-19T10:30:00.000Z',
    capturedAt = Date.now(),
    isReply = false,
    isRetweet = false,
    isQuoteTweet = false,
    isThread = false,
    hasImage = false,
    hasVideo = false,
    hasLink = false
  } = options;

  return {
    tweetId,
    tweetUrl,
    tweetText,
    authorUsername,
    authorDisplayName,
    timestamp,
    capturedAt,
    isReply,
    isRetweet,
    isQuoteTweet,
    isThread,
    threadId: tweetId,
    parentTweetId: null,
    conversationId: tweetId,
    hasImage,
    hasVideo,
    hasLink
  };
}

/**
 * Mock Chrome storage get
 */
function mockStorageGet(data) {
  global.chrome.storage.local.get.mockImplementation((keys, callback) => {
    const result = typeof keys === 'string' ? { [keys]: data } : data;
    if (callback) callback(result);
    return Promise.resolve(result);
  });
}

/**
 * Mock Chrome storage set
 */
function mockStorageSet() {
  global.chrome.storage.local.set.mockImplementation((items, callback) => {
    if (callback) callback();
    return Promise.resolve();
  });
}

/**
 * Mock fetch API
 */
function mockFetch(response, options = {}) {
  const { status = 200, ok = true } = options;

  global.fetch = jest.fn(() =>
    Promise.resolve({
      ok,
      status,
      json: () => Promise.resolve(response)
    })
  );
}

/**
 * Wait for a promise to resolve
 */
function waitFor(ms = 0) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Flush all pending promises
 */
async function flushPromises() {
  return new Promise(resolve => setImmediate(resolve));
}

// Export all helper functions
module.exports = {
  createMockTweetArticle,
  createMockLikeButton,
  createMockAuthState,
  createMockTweetData,
  mockStorageGet,
  mockStorageSet,
  mockFetch,
  waitFor,
  flushPromises
};
