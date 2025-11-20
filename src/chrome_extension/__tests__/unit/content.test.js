/**
 * Unit Tests for content.js
 * Tests DOM manipulation and tweet extraction functions
 */

const {
  extractTweetIdFromUrl,
  findTweetArticle,
  findLikeButton,
  extractTweetData,
  extractParentTweetId
} = require('../../content.js');

const { createMockTweetArticle, createMockLikeButton } = require('../helpers.js');

describe('extractTweetIdFromUrl', () => {

  test('should extract tweet ID from x.com URL', () => {
    const url = 'https://x.com/elonmusk/status/1234567890123456789';
    expect(extractTweetIdFromUrl(url)).toBe('1234567890123456789');
  });

  test('should extract tweet ID from twitter.com URL', () => {
    const url = 'https://twitter.com/user/status/9876543210';
    expect(extractTweetIdFromUrl(url)).toBe('9876543210');
  });

  test('should handle URLs with query parameters', () => {
    const url = 'https://x.com/user/status/1234567890?s=20&t=abc';
    expect(extractTweetIdFromUrl(url)).toBe('1234567890');
  });

  test('should return null for invalid URLs', () => {
    expect(extractTweetIdFromUrl('https://x.com/user')).toBeNull();
    expect(extractTweetIdFromUrl('https://example.com')).toBeNull();
    expect(extractTweetIdFromUrl('')).toBeNull();
  });

  test('should handle mobile URLs', () => {
    const url = 'https://mobile.x.com/user/status/1111111111';
    expect(extractTweetIdFromUrl(url)).toBe('1111111111');
  });
});

describe('DOM-based Tweet Extraction', () => {
  beforeEach(() => {
    // Set up DOM
    document.body.innerHTML = '';
  });

  describe('findTweetArticle', () => {
    test('should find tweet article from nested element', () => {
      const article = createMockTweetArticle();
      const button = createMockLikeButton();
      article.appendChild(button);
      document.body.appendChild(article);

      const found = findTweetArticle(button);

      expect(found).toBe(article);
      expect(found.getAttribute('data-testid')).toBe('tweet');
    });

    test('should return null if no article found within depth limit', () => {
      const div = document.createElement('div');
      const button = createMockLikeButton();
      div.appendChild(button);
      document.body.appendChild(div);

      const found = findTweetArticle(button);

      expect(found).toBeNull();
    });
  });

  describe('extractTweetData', () => {
    test('should extract all tweet metadata correctly', () => {
      const article = createMockTweetArticle({
        tweetId: '1234567890',
        tweetText: 'This is a test tweet with #hashtags',
        authorUsername: 'testuser',
        authorDisplayName: 'Test User',
        timestamp: '2024-11-19T10:30:00.000Z'
      });

      document.body.appendChild(article);

      const tweetData = extractTweetData(article);

      expect(tweetData).not.toBeNull();
      expect(tweetData.tweetId).toBe('1234567890');
      expect(tweetData.tweetText).toBe('This is a test tweet with #hashtags');
      expect(tweetData.authorDisplayName).toBe('Test User');
      expect(tweetData.authorUsername).toBe('testuser');
      expect(tweetData.timestamp).toBe('2024-11-19T10:30:00.000Z');
    });

    test('should detect reply tweets', () => {
      const article = createMockTweetArticle({
        tweetId: '1234567890',
        isReply: true
      });
      document.body.appendChild(article);

      const tweetData = extractTweetData(article);

      expect(tweetData).not.toBeNull();
      expect(tweetData.isReply).toBe(true);
    });

    test('should detect tweets with images', () => {
      const article = createMockTweetArticle({
        tweetId: '1234567890',
        hasImage: true
      });
      document.body.appendChild(article);

      const tweetData = extractTweetData(article);

      expect(tweetData).not.toBeNull();
      expect(tweetData.hasImage).toBe(true);
    });

    test('should detect tweets with videos', () => {
      const article = createMockTweetArticle({
        tweetId: '1234567890',
        hasVideo: true
      });
      document.body.appendChild(article);

      const tweetData = extractTweetData(article);

      expect(tweetData).not.toBeNull();
      expect(tweetData.hasVideo).toBe(true);
    });

    test('should handle tweets with long text', () => {
      const longText = 'A'.repeat(280);
      const article = createMockTweetArticle({
        tweetId: '1234567890',
        tweetText: longText
      });
      document.body.appendChild(article);

      const tweetData = extractTweetData(article);

      expect(tweetData).not.toBeNull();
      expect(tweetData.tweetText).toBe(longText);
      expect(tweetData.tweetText.length).toBe(280);
    });

    test('should handle tweets with special characters', () => {
      const specialText = 'Tweet with émojis 🎉 and spëcial çhars!';
      const article = createMockTweetArticle({
        tweetId: '1234567890',
        tweetText: specialText
      });
      document.body.appendChild(article);

      const tweetData = extractTweetData(article);

      expect(tweetData).not.toBeNull();
      expect(tweetData.tweetText).toBe(specialText);
    });

    test('should return null for missing tweet ID', () => {
      const article = document.createElement('article');
      article.setAttribute('data-testid', 'tweet');
      document.body.appendChild(article);

      const tweetData = extractTweetData(article);

      expect(tweetData).toBeNull();
    });
  });

  describe('findLikeButton', () => {
    test('should find like button with data-testid="like"', () => {
      const button = createMockLikeButton(false);
      const container = document.createElement('div');
      container.appendChild(button);
      document.body.appendChild(container);

      // Find button from nested element
      const span = document.createElement('span');
      button.appendChild(span);

      const found = findLikeButton(span);

      expect(found).toBe(button);
      expect(found.getAttribute('data-testid')).toBe('like');
    });

    test('should find unlike button (already liked)', () => {
      const button = createMockLikeButton(true);
      document.body.appendChild(button);

      const found = findLikeButton(button);

      expect(found).toBe(button);
      expect(found.getAttribute('data-testid')).toBe('unlike');
    });

    test('should return null if no like button found', () => {
      const div = document.createElement('div');
      document.body.appendChild(div);

      const found = findLikeButton(div);

      expect(found).toBeNull();
    });
  });
});

describe('Tweet Text Extraction Methods', () => {
  test('should extract text using textContent', () => {
    const article = createMockTweetArticle({
      tweetText: 'Simple tweet text'
    });
    document.body.appendChild(article);

    const tweetTextElement = article.querySelector('[data-testid="tweetText"]');
    const textContent = tweetTextElement?.textContent || '';

    expect(textContent).toBe('Simple tweet text');
  });

  test('should handle empty tweet text', () => {
    const article = createMockTweetArticle({ tweetText: '' });
    document.body.appendChild(article);

    const tweetTextElement = article.querySelector('[data-testid="tweetText"]');
    let tweetText = tweetTextElement?.textContent || '';

    if (!tweetText || tweetText.length < 10) {
      tweetText = tweetTextElement?.innerText || '';
    }

    expect(tweetText).toBe('');
  });

  test('should extract text from spans as fallback', () => {
    const div = document.createElement('div');
    div.setAttribute('data-testid', 'tweetText');

    const span1 = document.createElement('span');
    span1.textContent = 'Part 1 ';
    const span2 = document.createElement('span');
    span2.textContent = 'Part 2';

    div.appendChild(span1);
    div.appendChild(span2);
    document.body.appendChild(div);

    const spans = div.querySelectorAll('span');
    const combinedText = Array.from(spans)
      .map(span => span.textContent)
      .filter(text => text && text.trim())
      .join(' ');

    expect(combinedText).toBe('Part 1  Part 2');
  });

  test('should handle multiline tweets', () => {
    const multilineText = 'Line 1\nLine 2\nLine 3';
    const article = createMockTweetArticle({ tweetText: multilineText });
    document.body.appendChild(article);

    const tweetTextElement = article.querySelector('[data-testid="tweetText"]');
    const tweetText = tweetTextElement?.textContent;

    expect(tweetText).toContain('Line 1');
    expect(tweetText).toContain('Line 2');
    expect(tweetText).toContain('Line 3');
  });
});

describe('Tweet Type Detection', () => {
  test('should detect regular tweets', () => {
    const article = createMockTweetArticle({
      isReply: false,
      hasImage: false,
      hasVideo: false
    });
    document.body.appendChild(article);

    const isReply = !!article.querySelector('[data-testid="reply"]');
    const isRetweet = !!article.querySelector('[data-testid="socialContext"]');
    const hasImage = !!article.querySelector('[data-testid="tweetPhoto"]');
    const hasVideo = !!article.querySelector('[data-testid="videoPlayer"]');

    expect(isReply).toBe(false);
    expect(isRetweet).toBe(false);
    expect(hasImage).toBe(false);
    expect(hasVideo).toBe(false);
  });

  test('should detect quote tweets', () => {
    const article = createMockTweetArticle();

    // Add a nested tweet to make it a quote tweet
    const quotedTweet = document.createElement('article');
    quotedTweet.setAttribute('data-testid', 'tweet');
    article.appendChild(quotedTweet);

    document.body.appendChild(article);

    // querySelectorAll finds descendants only, so length >= 1 means there's a nested tweet
    const tweetArticles = article.querySelectorAll('[data-testid="tweet"]');
    const isQuoteTweet = tweetArticles.length >= 1;

    expect(isQuoteTweet).toBe(true);
    expect(tweetArticles.length).toBe(1); // Should find the nested quoted tweet
  });

  test('should detect media in tweets', () => {
    const article = createMockTweetArticle({
      hasImage: true,
      hasVideo: true
    });
    document.body.appendChild(article);

    const hasImage = !!article.querySelector('[data-testid="tweetPhoto"]');
    const hasVideo = !!article.querySelector('[data-testid="videoPlayer"]');

    expect(hasImage).toBe(true);
    expect(hasVideo).toBe(true);
  });
});
