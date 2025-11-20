/**
 * Jest Configuration for X Likes Capture Extension
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',

  // Root directory
  rootDir: '.',

  // Test match patterns
  testMatch: [
    '**/__tests__/**/*.test.js',
    '**/?(*.)+(spec|test).js'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'utils.js',
    'content.js',
    // Exclude UI/integration files - these need E2E tests, not unit tests
    '!background.js',
    '!popup.js',
    '!options.js',
    '!**/__tests__/**',
    '!**/__mocks__/**',
    '!**/node_modules/**',
    '!**/test_backend/**'
  ],

  // Coverage thresholds
  coverageThreshold: {
    // Only enforce thresholds on files we're actively testing
    './utils.js': {
      branches: 80,
      functions: 80,
      lines: 88,
      statements: 89
    },
    './content.js': {
      branches: 40,
      functions: 40,
      lines: 50,
      statements: 50
    }
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],

  // Module paths
  modulePaths: ['<rootDir>'],

  // Transform files
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/test_backend/'
  ],

  // Coverage directory
  coverageDirectory: '<rootDir>/coverage',

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,

  // Reset mocks between tests
  resetMocks: true,

  // Restore mocks between tests
  restoreMocks: true
};
