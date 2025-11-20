# Test Suite - X Likes Capture Extension

Complete testing documentation for the Chrome extension unit tests.

## 🎯 Overview

This test suite uses **Jest** with **jsdom** to test the Chrome extension code in isolation.

**Test Coverage:**
- ✅ All utility functions (`utils.js`)
- ✅ DOM extraction logic (`content.js`)
- ✅ Chrome API interactions (mocked)
- ✅ Error handling
- ✅ Edge cases

## 📦 Installation

### Install Dependencies

```bash
cd src/chrome_extension
npm install
```

This installs:
- `jest` - Test runner
- `@testing-library/dom` - DOM testing utilities
- `jest-chrome` - Chrome API mocks
- `babel-jest` - ES6+ support
- `jsdom` - DOM implementation for Node.js

## 🚀 Running Tests

### Run All Tests

```bash
npm test
```

### Run Tests in Watch Mode

```bash
npm run test:watch
```

Auto-reruns tests when files change. Great for TDD!

### Run with Coverage

```bash
npm run test:coverage
```

Generates coverage report in `coverage/` directory.

### Run Only Unit Tests

```bash
npm run test:unit
```

### Run Verbose Mode

```bash
npm run test:verbose
```

Shows detailed test output.

### Run Specific Test File

```bash
npm test utils.test.js
npm test content.test.js
```

## 📊 Coverage Reports

After running `npm run test:coverage`, open:

```bash
open coverage/lcov-report/index.html
```

**Coverage Goals:**
- Lines: 80%+
- Functions: 80%+
- Branches: 70%+
- Statements: 80%+

## 📁 Test Structure

```
__tests__/
├── unit/                  # Unit tests
│   ├── utils.test.js      # Tests for utils.js
│   └── content.test.js    # Tests for content.js
├── integration/           # Integration tests (future)
├── __mocks__/            # Mock modules
├── helpers.js            # Test helpers and fixtures
├── setup.js              # Jest setup (runs before all tests)
└── README.md             # This file
```

## 🧪 Test Examples

### Testing a Pure Function

```javascript
describe('formatTimeAgo', () => {
  test('should return "Just now" for recent timestamps', () => {
    const now = new Date();
    const recent = new Date(now.getTime() - 30 * 1000);

    expect(formatTimeAgo(recent)).toBe('Just now');
  });
});
```

### Testing with Chrome API Mocks

```javascript
describe('getAuthState', () => {
  test('should return auth from storage', async () => {
    const mockAuth = { accessToken: 'token123' };
    chrome.storage.local.get.mockResolvedValue({ auth: mockAuth });

    const result = await getAuthState();
    expect(result).toEqual(mockAuth);
  });
});
```

### Testing DOM Extraction

```javascript
describe('extractTweetData', () => {
  test('should extract tweet metadata', () => {
    const article = createMockTweetArticle({
      tweetId: '123',
      tweetText: 'Test tweet'
    });
    document.body.appendChild(article);

    const tweetId = extractTweetId(article);
    expect(tweetId).toBe('123');
  });
});
```

## 🛠️ Test Helpers

### Available Helpers (from `helpers.js`)

**DOM Creation:**
- `createMockTweetArticle(options)` - Create a mock tweet article element
- `createMockLikeButton(liked)` - Create a mock like button

**Data Creation:**
- `createMockAuthState(options)` - Create mock auth data
- `createMockTweetData(options)` - Create mock tweet data

**Chrome API Mocking:**
- `mockStorageGet(data)` - Mock chrome.storage.local.get
- `mockStorageSet()` - Mock chrome.storage.local.set
- `mockFetch(response, options)` - Mock fetch API

**Utilities:**
- `waitFor(ms)` - Wait for a specific time
- `flushPromises()` - Flush all pending promises

### Example Usage

```javascript
import { createMockTweetArticle, mockStorageGet } from '../helpers';

test('extract tweet from article', () => {
  const article = createMockTweetArticle({
    tweetId: '123',
    tweetText: 'Hello World',
    authorUsername: 'testuser'
  });

  // Use article in test...
});

test('get user settings', async () => {
  mockStorageGet({ settings: { debugMode: true } });

  const settings = await getSettings();
  expect(settings.debugMode).toBe(true);
});
```

## 🎨 Writing Good Tests

### DO ✅

**Test behavior, not implementation:**
```javascript
// GOOD
test('should format 5 minutes correctly', () => {
  const time = Date.now() - (5 * 60 * 1000);
  expect(formatTimeAgo(time)).toBe('5 mins ago');
});
```

**Use descriptive test names:**
```javascript
test('should return null if tweet ID not found in URL', () => {
  // ...
});
```

**Test edge cases:**
```javascript
test('should handle empty string', () => {
  expect(sanitizeText('')).toBe('');
});

test('should handle null', () => {
  expect(sanitizeText(null)).toBe('');
});
```

### DON'T ❌

**Don't test implementation details:**
```javascript
// BAD
test('should call querySelector', () => {
  expect(element.querySelector).toHaveBeenCalled();
});
```

**Don't write vague tests:**
```javascript
// BAD
test('works correctly', () => {
  // What does "works correctly" mean?
});
```

**Don't skip cleanup:**
```javascript
// BAD - No cleanup
test('test DOM', () => {
  document.body.innerHTML = '<div>test</div>';
  // Cleanup missing!
});

// GOOD
afterEach(() => {
  document.body.innerHTML = '';
});
```

## 🔍 Debugging Tests

### Run Specific Test

```bash
npm test -- --testNamePattern="should format time"
```

### Run in Debug Mode

```bash
npm run test:debug
```

Then open `chrome://inspect` in Chrome.

### Add Debug Breakpoints

```javascript
test('my test', () => {
  debugger; // Execution will pause here
  // ...
});
```

### Use console.log (Temporarily)

```javascript
test('my test', () => {
  const result = myFunction();
  console.log('Result:', result);
  expect(result).toBe(expected);
});
```

## 📈 Coverage Thresholds

Configured in `jest.config.js`:

```javascript
coverageThreshold: {
  global: {
    branches: 70,
    functions: 80,
    lines: 80,
    statements: 80
  }
}
```

Tests will **fail** if coverage drops below these thresholds.

## 🚨 Common Issues

### Issue: "ReferenceError: chrome is not defined"

**Solution**: Chrome API is mocked in `setup.js`. Make sure setup is running:
```javascript
// Check jest.config.js
setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js']
```

### Issue: "Cannot find module '../helpers'"

**Solution**: Use relative import path:
```javascript
import { createMockTweetArticle } from '../helpers';
```

### Issue: Tests pass locally but fail in CI

**Solution**: Check for:
- Time-dependent tests (use fixed dates)
- Random data (use seeded random or fixtures)
- File system dependencies

### Issue: "document is not defined"

**Solution**: Make sure `testEnvironment: 'jsdom'` in jest.config.js

## 🔄 Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd src/chrome_extension && npm install
      - run: cd src/chrome_extension && npm test
      - run: cd src/chrome_extension && npm run test:coverage
```

## 📚 Additional Resources

### Jest Documentation
- [Getting Started](https://jestjs.io/docs/getting-started)
- [Expect API](https://jestjs.io/docs/expect)
- [Mock Functions](https://jestjs.io/docs/mock-functions)

### Testing Library
- [@testing-library/dom](https://testing-library.com/docs/dom-testing-library/intro)
- [Testing Queries](https://testing-library.com/docs/queries/about)

### Chrome Extension Testing
- [Chrome Extensions Testing Guide](https://developer.chrome.com/docs/extensions/mv3/tut_testing/)

## ✅ Next Steps

1. **Run the tests**: `npm test`
2. **Check coverage**: `npm run test:coverage`
3. **Add more tests**: Create tests for `background.js` and `popup.js`
4. **Set up CI**: Add GitHub Actions
5. **Write integration tests**: Test component interactions

---

**Happy Testing! 🎉**
