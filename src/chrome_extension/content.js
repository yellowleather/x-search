/**
 * Content Script for X Likes Capture Extension
 * Monitors X.com DOM for like actions and extracts tweet metadata
 */

// Track processed tweets to avoid duplicates
const processedTweets = new Set();

// Debounce timer for like actions
let likeDebounceTimer = null;

/**
 * Initialize the content script
 */
function init() {
  console.log('[X Likes Capture] Content script loaded');

  // Monitor for like button clicks
  document.addEventListener('click', handleClick, true);

  // Also use MutationObserver to catch dynamic content
  observeLikeButtons();
}

/**
 * Handle click events to detect likes
 * @param {Event} event - Click event
 */
function handleClick(event) {
  const target = event.target;

  // Find the like button (it might be nested in SVG or spans)
  const likeButton = findLikeButton(target);

  if (likeButton) {
    // Debounce to avoid multiple captures
    clearTimeout(likeDebounceTimer);
    likeDebounceTimer = setTimeout(() => {
      handleLikeAction(likeButton);
    }, 500);
  }
}

/**
 * Find the like button element from click target
 * @param {Element} element - Clicked element
 * @returns {Element|null} Like button element or null
 */
function findLikeButton(element) {
  // Traverse up to find button with data-testid="like"
  let current = element;
  let depth = 0;

  while (current && depth < 10) {
    const testId = current.getAttribute('data-testid');

    if (testId === 'like' || testId === 'unlike') {
      return current;
    }

    current = current.parentElement;
    depth++;
  }

  return null;
}

/**
 * Handle like action on a tweet
 * @param {Element} likeButton - The like button element
 */
function handleLikeAction(likeButton) {
  // Check if this is a "like" action (not "unlike")
  const testId = likeButton.getAttribute('data-testid');

  // We capture when user clicks "like" button
  // After clicking, it changes from "like" to "unlike"
  if (testId === 'like') {
    // Find the tweet article element
    const tweetArticle = findTweetArticle(likeButton);

    if (tweetArticle) {
      captureTweet(tweetArticle);
    }
  }
}

/**
 * Find the tweet article element from like button
 * @param {Element} likeButton - Like button element
 * @returns {Element|null} Tweet article element or null
 */
function findTweetArticle(likeButton) {
  let current = likeButton;
  let depth = 0;

  while (current && depth < 20) {
    if (current.tagName === 'ARTICLE' && current.getAttribute('data-testid') === 'tweet') {
      return current;
    }

    current = current.parentElement;
    depth++;
  }

  return null;
}

/**
 * Extract tweet metadata and send to background
 * @param {Element} tweetArticle - Tweet article element
 */
function captureTweet(tweetArticle) {
  try {
    const tweetData = extractTweetData(tweetArticle);

    if (!tweetData || !tweetData.tweetId) {
      console.warn('[X Likes Capture] Could not extract tweet data');
      return;
    }

    // Check if already processed
    if (processedTweets.has(tweetData.tweetId)) {
      console.log('[X Likes Capture] Tweet already processed:', tweetData.tweetId);
      return;
    }

    // Mark as processed
    processedTweets.add(tweetData.tweetId);

    // Send to background worker
    chrome.runtime.sendMessage({
      action: 'captureTweet',
      data: tweetData
    }, response => {
      if (chrome.runtime.lastError) {
        console.error('[X Likes Capture] Error sending message:', chrome.runtime.lastError);
        return;
      }

      if (response && response.success) {
        console.log('[X Likes Capture] Tweet captured:', tweetData.tweetId);
        showCaptureIndicator(tweetArticle);
      } else {
        console.warn('[X Likes Capture] Capture failed:', response?.error);
      }
    });

  } catch (error) {
    console.error('[X Likes Capture] Error capturing tweet:', error);
  }
}

/**
 * Extract tweet metadata from article element
 * @param {Element} article - Tweet article element
 * @returns {Object|null} Tweet data object or null
 */
function extractTweetData(article) {
  try {
    // Extract tweet URL and ID
    const timeElement = article.querySelector('time');
    const linkElement = timeElement?.parentElement;
    const tweetUrl = linkElement?.href || '';
    const tweetId = extractTweetIdFromUrl(tweetUrl);

    if (!tweetId) {
      console.warn('[X Likes Capture] Could not find tweet ID');
      return null;
    }

    // Extract tweet text
    // Try multiple methods to get the full text (handles truncated tweets)
    const tweetTextElement = article.querySelector('[data-testid="tweetText"]');
    let tweetText = '';

    if (tweetTextElement) {
      // Method 1: Try textContent (gets all text including hidden)
      tweetText = tweetTextElement.textContent || '';

      // Method 2: If text seems truncated, try innerText
      if (!tweetText || tweetText.length < 10) {
        tweetText = tweetTextElement.innerText || '';
      }

      // Method 3: Get all span elements and combine their text
      // This helps with tweets that have special formatting
      if (!tweetText) {
        const spans = tweetTextElement.querySelectorAll('span');
        tweetText = Array.from(spans)
          .map(span => span.textContent)
          .filter(text => text && text.trim())
          .join(' ');
      }
    }

    // Log for debugging
    console.log('[X Likes Capture] Captured text length:', tweetText.length);

    // Extract author info
    const authorElements = article.querySelectorAll('[data-testid="User-Name"] a');
    let authorUsername = '';
    let authorDisplayName = '';

    if (authorElements.length > 0) {
      // First link is display name
      authorDisplayName = authorElements[0].textContent || '';

      // Username is in the second span or link
      const usernameElement = Array.from(authorElements).find(
        el => el.textContent.startsWith('@')
      );
      authorUsername = usernameElement?.textContent.replace('@', '') || '';
    }

    // Extract timestamp
    const timestamp = timeElement?.getAttribute('datetime') || new Date().toISOString();

    // Detect tweet type
    const isReply = !!article.querySelector('[data-testid="reply"]');
    const isRetweet = !!article.querySelector('[data-testid="socialContext"]');
    const isQuoteTweet = article.querySelectorAll('[data-testid="tweet"]').length > 1;

    // Detect media
    const hasImage = !!article.querySelector('[data-testid="tweetPhoto"]');
    const hasVideo = !!article.querySelector('[data-testid="videoPlayer"]');
    const hasLink = !!article.querySelector('[data-testid="card.wrapper"]');

    // Extract thread/conversation context
    const conversationId = tweetId; // Default to tweet ID
    const threadId = tweetId;
    const parentTweetId = isReply ? extractParentTweetId(article) : null;

    const tweetData = {
      // Core identifiers
      tweetId,
      tweetUrl,

      // Content
      tweetText,

      // Author info
      authorUsername,
      authorDisplayName,

      // Timestamps
      timestamp,
      capturedAt: Date.now(),

      // Context flags
      isReply,
      isRetweet,
      isQuoteTweet,
      isThread: false, // Would need more logic to detect

      // Thread/conversation context
      threadId,
      parentTweetId,
      conversationId,

      // Media indicators
      hasImage,
      hasVideo,
      hasLink
    };

    return tweetData;

  } catch (error) {
    console.error('[X Likes Capture] Error extracting tweet data:', error);
    return null;
  }
}

/**
 * Extract tweet ID from URL
 * @param {string} url - Tweet URL
 * @returns {string|null} Tweet ID or null
 */
function extractTweetIdFromUrl(url) {
  const match = url.match(/status\/(\d+)/);
  return match ? match[1] : null;
}

/**
 * Extract parent tweet ID if this is a reply
 * @param {Element} article - Tweet article element
 * @returns {string|null} Parent tweet ID or null
 */
function extractParentTweetId(article) {
  // This is tricky - X doesn't always show parent ID directly
  // Would need to look at the conversation structure
  // For now, return null
  return null;
}

/**
 * Show visual indicator that tweet was captured
 * @param {Element} article - Tweet article element
 */
function showCaptureIndicator(article) {
  // Find like button area
  const likeButton = article.querySelector('[data-testid="unlike"]');

  if (likeButton) {
    // Add a subtle checkmark indicator
    const indicator = document.createElement('span');
    indicator.textContent = '✓';
    indicator.style.cssText = `
      position: absolute;
      top: -8px;
      right: -8px;
      background: #1d9bf0;
      color: white;
      border-radius: 50%;
      width: 16px;
      height: 16px;
      font-size: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      animation: fadeOut 2s forwards;
    `;

    // Add fadeOut animation
    const style = document.createElement('style');
    style.textContent = `
      @keyframes fadeOut {
        0% { opacity: 1; }
        70% { opacity: 1; }
        100% { opacity: 0; }
      }
    `;
    document.head.appendChild(style);

    // Position relative to like button
    const buttonParent = likeButton.parentElement;
    if (buttonParent) {
      buttonParent.style.position = 'relative';
      buttonParent.appendChild(indicator);

      // Remove after animation
      setTimeout(() => {
        indicator.remove();
      }, 2000);
    }
  }
}

/**
 * Use MutationObserver to watch for like button state changes
 */
function observeLikeButtons() {
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      // Check if a like button changed to unlike
      if (mutation.type === 'attributes' && mutation.attributeName === 'data-testid') {
        const element = mutation.target;
        const newTestId = element.getAttribute('data-testid');
        const oldTestId = mutation.oldValue;

        if (oldTestId === 'like' && newTestId === 'unlike') {
          // Like action detected
          const tweetArticle = findTweetArticle(element);
          if (tweetArticle) {
            captureTweet(tweetArticle);
          }
        }
      }
    });
  });

  // Observe the entire document for like button changes
  observer.observe(document.body, {
    attributes: true,
    attributeOldValue: true,
    attributeFilter: ['data-testid'],
    subtree: true
  });

  console.log('[X Likes Capture] MutationObserver initialized');
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

// Export functions for testing (Node.js environment only)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    extractTweetIdFromUrl,
    findTweetArticle,
    findLikeButton,
    extractTweetData,
    extractParentTweetId
  };
}
