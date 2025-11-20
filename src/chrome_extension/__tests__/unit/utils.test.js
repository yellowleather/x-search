/**
 * Unit Tests for utils.js
 * Tests all utility functions by importing the actual source file
 */

// Import the actual functions from source
const {
  formatTimeAgo,
  isTokenExpired,
  isValidEmail,
  sanitizeText,
  extractTweetId,
  getErrorMessage,
  getAuthState,
  saveAuthState,
  clearAuth,
  getSettings,
  saveSettings,
  getStats,
  updateStats
} = require('../../utils.js');

describe('formatTimeAgo', () => {
  test('should return "Just now" for timestamps less than 60 seconds ago', () => {
    const now = new Date();
    const recentTime = new Date(now.getTime() - 30 * 1000); // 30 seconds ago

    expect(formatTimeAgo(recentTime)).toBe('Just now');
  });

  test('should return minutes for timestamps less than 1 hour ago', () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

    expect(formatTimeAgo(fiveMinutesAgo)).toBe('5 mins ago');
  });

  test('should return singular "min" for 1 minute', () => {
    const now = new Date();
    const oneMinuteAgo = new Date(now.getTime() - 1 * 60 * 1000);

    expect(formatTimeAgo(oneMinuteAgo)).toBe('1 min ago');
  });

  test('should return hours for timestamps less than 24 hours ago', () => {
    const now = new Date();
    const twoHoursAgo = new Date(now.getTime() - 2 * 60 * 60 * 1000);

    expect(formatTimeAgo(twoHoursAgo)).toBe('2 hours ago');
  });

  test('should return singular "hour" for 1 hour', () => {
    const now = new Date();
    const oneHourAgo = new Date(now.getTime() - 1 * 60 * 60 * 1000);

    expect(formatTimeAgo(oneHourAgo)).toBe('1 hour ago');
  });

  test('should return days for timestamps less than 30 days ago', () => {
    const now = new Date();
    const fiveDaysAgo = new Date(now.getTime() - 5 * 24 * 60 * 60 * 1000);

    expect(formatTimeAgo(fiveDaysAgo)).toBe('5 days ago');
  });

  test('should return months for timestamps more than 30 days ago', () => {
    const now = new Date();
    const twoMonthsAgo = new Date(now.getTime() - 60 * 24 * 60 * 60 * 1000);

    expect(formatTimeAgo(twoMonthsAgo)).toBe('2 months ago');
  });

  test('should accept Date objects', () => {
    const now = new Date();
    const date = new Date(now.getTime() - 10 * 60 * 1000);

    expect(formatTimeAgo(date)).toBe('10 mins ago');
  });

  test('should accept timestamps as numbers', () => {
    const now = Date.now();
    const timestamp = now - (10 * 60 * 1000);

    expect(formatTimeAgo(timestamp)).toBe('10 mins ago');
  });
});

describe('isTokenExpired', () => {
  test('should return true if token is already expired', () => {
    const pastTime = Date.now() - 10000; // 10 seconds ago

    expect(isTokenExpired(pastTime)).toBe(true);
  });

  test('should return true if token expires within buffer time', () => {
    const soonToExpire = Date.now() + 30000; // 30 seconds from now
    const buffer = 60; // 60 seconds buffer

    expect(isTokenExpired(soonToExpire, buffer)).toBe(true);
  });

  test('should return false if token is not expired and outside buffer', () => {
    const futureTime = Date.now() + 3600000; // 1 hour from now

    expect(isTokenExpired(futureTime)).toBe(false);
  });

  test('should use default buffer of 60 seconds', () => {
    const almostExpired = Date.now() + 30000; // 30 seconds from now

    expect(isTokenExpired(almostExpired)).toBe(true);
  });

  test('should allow custom buffer time', () => {
    const futureTime = Date.now() + 45000; // 45 seconds from now

    expect(isTokenExpired(futureTime, 30)).toBe(false);
    expect(isTokenExpired(futureTime, 60)).toBe(true);
  });
});

describe('isValidEmail', () => {
  test('should return true for valid email addresses', () => {
    expect(isValidEmail('test@example.com')).toBe(true);
    expect(isValidEmail('user.name@domain.co.uk')).toBe(true);
    expect(isValidEmail('user+tag@example.org')).toBe(true);
  });

  test('should return false for invalid email addresses', () => {
    expect(isValidEmail('not-an-email')).toBe(false);
    expect(isValidEmail('missing@domain')).toBe(false);
    expect(isValidEmail('@nodomain.com')).toBe(false);
    expect(isValidEmail('noat.domain.com')).toBe(false);
    expect(isValidEmail('')).toBe(false);
  });

  test('should return false for emails with spaces', () => {
    expect(isValidEmail('user @example.com')).toBe(false);
    expect(isValidEmail('user@exam ple.com')).toBe(false);
  });
});

describe('sanitizeText', () => {
  test('should remove < and > characters', () => {
    expect(sanitizeText('<script>alert("xss")</script>')).toBe('scriptalert("xss")/script');
    expect(sanitizeText('Hello <b>World</b>')).toBe('Hello bWorld/b');
  });

  test('should return empty string for null or undefined', () => {
    expect(sanitizeText(null)).toBe('');
    expect(sanitizeText(undefined)).toBe('');
    expect(sanitizeText('')).toBe('');
  });

  test('should not affect text without < or >', () => {
    expect(sanitizeText('Normal text')).toBe('Normal text');
    expect(sanitizeText('Text with @mentions and #hashtags')).toBe('Text with @mentions and #hashtags');
  });
});

describe('extractTweetId', () => {
  test('should extract tweet ID from valid X.com URL', () => {
    const url = 'https://x.com/user/status/1234567890123456789';
    expect(extractTweetId(url)).toBe('1234567890123456789');
  });

  test('should extract tweet ID from valid twitter.com URL', () => {
    const url = 'https://twitter.com/user/status/9876543210987654321';
    expect(extractTweetId(url)).toBe('9876543210987654321');
  });

  test('should return null for invalid URLs', () => {
    expect(extractTweetId('https://x.com/user')).toBeNull();
    expect(extractTweetId('not a url')).toBeNull();
    expect(extractTweetId('')).toBeNull();
  });

  test('should handle URLs with query parameters', () => {
    const url = 'https://x.com/user/status/1234567890?s=20';
    expect(extractTweetId(url)).toBe('1234567890');
  });
});

describe('getErrorMessage', () => {
  test('should return user-friendly message for fetch errors', () => {
    const error = new Error('Failed to fetch');
    expect(getErrorMessage(error)).toBe('Unable to connect to server. Please check your internet connection.');
  });

  test('should return user-friendly message for network errors', () => {
    const error = new Error('NetworkError when attempting to fetch resource');
    expect(getErrorMessage(error)).toBe('Network error. Please try again.');
  });

  test('should return appropriate message for 401 status', () => {
    const error = { status: 401 };
    expect(getErrorMessage(error)).toBe('Authentication failed. Please log in again.');
  });

  test('should return appropriate message for 404 status', () => {
    const error = { status: 404 };
    expect(getErrorMessage(error)).toBe('Server endpoint not found.');
  });

  test('should return appropriate message for 429 status', () => {
    const error = { status: 429 };
    expect(getErrorMessage(error)).toBe('Too many requests. Please wait a moment.');
  });

  test('should return appropriate message for 500 status', () => {
    const error = { status: 500 };
    expect(getErrorMessage(error)).toBe('Server error. Please try again later.');
  });

  test('should return generic message with status code for unknown status', () => {
    const error = { status: 418 };
    expect(getErrorMessage(error)).toBe('Server error (418)');
  });

  test('should return error message if available', () => {
    const error = { message: 'Custom error message' };
    expect(getErrorMessage(error)).toBe('Custom error message');
  });

  test('should return default message for null/undefined error', () => {
    expect(getErrorMessage(null)).toBe('An unknown error occurred');
    expect(getErrorMessage(undefined)).toBe('An unknown error occurred');
  });
});

// Storage function tests (using Chrome API mocks)
describe('Storage Functions', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getAuthState', () => {
    test('should return auth object if present', async () => {
      const mockAuth = {
        accessToken: 'token123',
        userId: 'user456'
      };

      chrome.storage.local.get.mockResolvedValue({ auth: mockAuth });

      const result = await getAuthState();
      expect(result).toEqual(mockAuth);
      expect(chrome.storage.local.get).toHaveBeenCalledWith(['auth']);
    });

    test('should return null if no auth present', async () => {
      chrome.storage.local.get.mockResolvedValue({});

      const result = await getAuthState();
      expect(result).toBeNull();
    });
  });

  describe('saveAuthState', () => {
    test('should save auth to storage', async () => {
      const mockAuth = { accessToken: 'token123' };

      await saveAuthState(mockAuth);

      expect(chrome.storage.local.set).toHaveBeenCalledWith({ auth: mockAuth });
    });
  });

  describe('clearAuth', () => {
    test('should remove auth from storage', async () => {
      await clearAuth();

      expect(chrome.storage.local.remove).toHaveBeenCalledWith(['auth']);
    });
  });

  describe('getSettings', () => {
    test('should return default settings if none stored', async () => {
      chrome.storage.local.get.mockResolvedValue({});

      const result = await getSettings();
      expect(result).toEqual({
        backendUrl: 'https://api.yourservice.com',
        captureEnabled: true
      });
    });

    test('should merge stored settings with defaults', async () => {
      chrome.storage.local.get.mockResolvedValue({
        settings: {
          backendUrl: 'https://custom.api.com',
          debugMode: true
        }
      });

      const result = await getSettings();
      expect(result).toEqual({
        backendUrl: 'https://custom.api.com',
        captureEnabled: true,
        debugMode: true
      });
    });
  });

  describe('saveSettings', () => {
    test('should save settings to storage', async () => {
      const settings = { backendUrl: 'https://custom.api.com' };

      await saveSettings(settings);

      expect(chrome.storage.local.set).toHaveBeenCalledWith({ settings });
    });
  });

  describe('getStats', () => {
    test('should return default stats if none stored', async () => {
      chrome.storage.local.get.mockResolvedValue({});

      const result = await getStats();
      expect(result).toEqual({
        totalCaptured: 0,
        totalSent: 0,
        queueSize: 0,
        lastCapture: null,
        lastSync: null
      });
    });

    test('should return stored stats', async () => {
      const mockStats = {
        totalCaptured: 10,
        totalSent: 8,
        queueSize: 2,
        lastCapture: Date.now(),
        lastSync: Date.now()
      };

      chrome.storage.local.get.mockResolvedValue({ stats: mockStats });

      const result = await getStats();
      expect(result).toEqual(mockStats);
    });
  });

  describe('updateStats', () => {
    beforeEach(() => {
      // Mock getStats to return default stats
      chrome.storage.local.get.mockResolvedValue({
        stats: {
          totalCaptured: 0,
          totalSent: 0,
          queueSize: 0,
          lastCapture: null,
          lastSync: null
        }
      });
    });

    test('should increment totalCaptured for "captured" action', async () => {
      await updateStats('captured');

      expect(chrome.storage.local.set).toHaveBeenCalledWith({
        stats: expect.objectContaining({
          totalCaptured: 1,
          lastCapture: expect.any(Number)
        })
      });
    });

    test('should increment totalSent for "sent" action', async () => {
      await updateStats('sent');

      expect(chrome.storage.local.set).toHaveBeenCalledWith({
        stats: expect.objectContaining({
          totalSent: 1,
          lastSync: expect.any(Number)
        })
      });
    });

    test('should increment queueSize for "queued" action', async () => {
      await updateStats('queued');

      expect(chrome.storage.local.set).toHaveBeenCalledWith({
        stats: expect.objectContaining({
          queueSize: 1
        })
      });
    });
  });
});
