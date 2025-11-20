/**
 * Popup UI Logic for X Likes Capture Extension
 * Handles authentication, status display, and user interactions
 */

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
  await initializePopup();
});

/**
 * Initialize the popup based on authentication state
 */
async function initializePopup() {
  try {
    // Show loading view
    showView('loadingView');

    // Check backend connectivity
    await checkBackendStatus();

    // Check authentication state
    const auth = await getAuthState();

    if (auth && auth.accessToken) {
      // User is authenticated
      await showAuthenticatedView();
      await loadStats();
      startAutoRefresh();
    } else {
      // User is not authenticated
      showLoginView();
    }

  } catch (error) {
    console.error('Error initializing popup:', error);
    showError('Failed to initialize extension');
    showLoginView();
  }
}

/**
 * Show login view
 */
function showLoginView() {
  showView('loginView');
  setupLoginHandlers();
}

/**
 * Show authenticated view
 */
async function showAuthenticatedView() {
  showView('authenticatedView');

  // Display user email
  const auth = await getAuthState();
  const userEmailEl = document.getElementById('userEmail');
  if (userEmailEl && auth) {
    userEmailEl.textContent = auth.email || 'Unknown';
  }

  setupAuthenticatedHandlers();
}

/**
 * Show specific view and hide others
 * @param {string} viewId - ID of view to show
 */
function showView(viewId) {
  const views = document.querySelectorAll('.view');
  views.forEach(view => {
    view.style.display = view.id === viewId ? 'block' : 'none';
  });
}

/**
 * Setup event handlers for login view
 */
function setupLoginHandlers() {
  const loginForm = document.getElementById('loginForm');
  const loginBtn = document.getElementById('loginBtn');
  const registerBtn = document.getElementById('registerBtn');

  // Login form submission
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      await handleLogin();
    });
  }

  // Register button
  if (registerBtn) {
    registerBtn.addEventListener('click', async () => {
      await handleRegister();
    });
  }
}

/**
 * Setup event handlers for authenticated view
 */
function setupAuthenticatedHandlers() {
  const logoutBtn = document.getElementById('logoutBtn');
  const retryBtn = document.getElementById('retryBtn');
  const settingsBtn = document.getElementById('settingsBtn');

  // Logout button
  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await handleLogout();
    });
  }

  // Retry queue button
  if (retryBtn) {
    retryBtn.addEventListener('click', async () => {
      await handleRetryQueue();
    });
  }

  // Settings button
  if (settingsBtn) {
    settingsBtn.addEventListener('click', () => {
      chrome.runtime.openOptionsPage();
    });
  }
}

/**
 * Handle login
 */
async function handleLogin() {
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const loginBtn = document.getElementById('loginBtn');

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  // Validate inputs
  if (!email || !password) {
    showError('Please enter email and password');
    return;
  }

  if (!isValidEmail(email)) {
    showError('Please enter a valid email address');
    return;
  }

  // Disable button and show loading
  loginBtn.disabled = true;
  loginBtn.textContent = 'Logging in...';
  hideError();

  try {
    const settings = await getSettings();
    const response = await fetch(`${settings.backendUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Invalid credentials');
    }

    const data = await response.json();

    // Save auth state
    await saveAuthState({
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      expiresAt: Date.now() + (data.expiresIn * 1000),
      userId: data.userId,
      email: email
    });

    // Switch to authenticated view
    await showAuthenticatedView();
    await loadStats();

    // Trigger queue retry
    chrome.runtime.sendMessage({ action: 'retryQueue' });

  } catch (error) {
    console.error('Login error:', error);
    showError(getErrorMessage(error));
    loginBtn.disabled = false;
    loginBtn.textContent = 'Login';
  }
}

/**
 * Handle registration
 */
async function handleRegister() {
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const registerBtn = document.getElementById('registerBtn');

  const email = emailInput.value.trim();
  const password = passwordInput.value;

  // Validate inputs
  if (!email || !password) {
    showError('Please enter email and password');
    return;
  }

  if (!isValidEmail(email)) {
    showError('Please enter a valid email address');
    return;
  }

  if (password.length < 8) {
    showError('Password must be at least 8 characters');
    return;
  }

  // Disable button and show loading
  registerBtn.disabled = true;
  registerBtn.textContent = 'Registering...';
  hideError();

  try {
    const settings = await getSettings();
    const response = await fetch(`${settings.backendUrl}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || 'Registration failed');
    }

    const data = await response.json();

    // Save auth state
    await saveAuthState({
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
      expiresAt: Date.now() + (data.expiresIn * 1000),
      userId: data.userId,
      email: email
    });

    // Switch to authenticated view
    await showAuthenticatedView();
    await loadStats();

  } catch (error) {
    console.error('Registration error:', error);
    showError(getErrorMessage(error));
    registerBtn.disabled = false;
    registerBtn.textContent = 'Register';
  }
}

/**
 * Handle logout
 */
async function handleLogout() {
  if (!confirm('Are you sure you want to logout?')) {
    return;
  }

  try {
    await clearAuth();
    showLoginView();
  } catch (error) {
    console.error('Logout error:', error);
    showError('Failed to logout');
  }
}

/**
 * Handle retry queue
 */
async function handleRetryQueue() {
  const retryBtn = document.getElementById('retryBtn');

  retryBtn.disabled = true;
  retryBtn.textContent = 'Retrying...';

  try {
    const response = await chrome.runtime.sendMessage({ action: 'retryQueue' });

    if (response.error) {
      throw new Error(response.error);
    }

    showNotificationUI(
      `Processed: ${response.processed}, Remaining: ${response.remaining}`,
      'success'
    );

    // Reload stats
    await loadStats();

  } catch (error) {
    console.error('Retry queue error:', error);
    showNotificationUI(getErrorMessage(error), 'error');
  } finally {
    retryBtn.disabled = false;
    retryBtn.textContent = 'Retry Queue';
  }
}

/**
 * Load and display statistics
 */
async function loadStats() {
  try {
    const stats = await getStats();
    const storage = await chrome.storage.local.get(['queue']);
    const queueSize = storage.queue?.length || 0;

    // Update counts
    const capturedEl = document.getElementById('capturedCount');
    const syncedEl = document.getElementById('syncedCount');
    const queuedEl = document.getElementById('queuedCount');

    if (capturedEl) capturedEl.textContent = stats.totalCaptured || 0;
    if (syncedEl) syncedEl.textContent = stats.totalSent || 0;
    if (queuedEl) queuedEl.textContent = queueSize;

    // Update last capture time
    const lastCaptureEl = document.getElementById('lastCapture');
    if (lastCaptureEl) {
      lastCaptureEl.textContent = stats.lastCapture
        ? formatTimeAgo(stats.lastCapture)
        : 'Never';
    }

    // Update last sync time
    const lastSyncEl = document.getElementById('lastSync');
    if (lastSyncEl) {
      lastSyncEl.textContent = stats.lastSync
        ? formatTimeAgo(stats.lastSync)
        : 'Never';
    }

    // Update status indicator
    updateStatusIndicator(queueSize);

  } catch (error) {
    console.error('Error loading stats:', error);
  }
}

/**
 * Update status indicator based on queue size
 * @param {number} queueSize - Number of items in queue
 */
function updateStatusIndicator(queueSize) {
  const statusIndicator = document.getElementById('statusIndicator');

  if (!statusIndicator) return;

  if (queueSize > 0) {
    statusIndicator.textContent = '⚠️ Queued';
    statusIndicator.className = 'status-badge status-queued';
  } else {
    statusIndicator.textContent = '✅ Active';
    statusIndicator.className = 'status-badge status-active';
  }
}

/**
 * Check backend status
 */
async function checkBackendStatus() {
  const statusEl = document.getElementById('backendStatus');

  if (!statusEl) return;

  try {
    const settings = await getSettings();

    // Try to fetch health endpoint
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${settings.backendUrl}/api/health`, {
      method: 'GET',
      signal: controller.signal
    }).catch(() => null);

    clearTimeout(timeoutId);

    const statusText = statusEl.querySelector('.status-text');
    const statusDot = statusEl.querySelector('.status-dot');

    if (response && response.ok) {
      statusText.textContent = 'Backend: Connected';
      statusDot.className = 'status-dot status-connected';
    } else {
      statusText.textContent = 'Backend: Offline';
      statusDot.className = 'status-dot status-offline';
    }

  } catch (error) {
    console.error('Backend health check failed:', error);
    const statusText = statusEl.querySelector('.status-text');
    const statusDot = statusEl.querySelector('.status-dot');

    statusText.textContent = 'Backend: Unknown';
    statusDot.className = 'status-dot status-offline';
  }
}

/**
 * Show error message in login view
 * @param {string} message - Error message
 */
function showError(message) {
  const errorEl = document.getElementById('loginError');
  if (errorEl) {
    errorEl.textContent = message;
    errorEl.style.display = 'block';
  }
}

/**
 * Hide error message
 */
function hideError() {
  const errorEl = document.getElementById('loginError');
  if (errorEl) {
    errorEl.style.display = 'none';
  }
}

/**
 * Show notification in authenticated view
 * @param {string} message - Notification message
 * @param {string} type - Notification type ('success', 'error', 'info')
 */
function showNotificationUI(message, type = 'info') {
  const notificationEl = document.getElementById('notificationArea');

  if (!notificationEl) return;

  notificationEl.textContent = message;
  notificationEl.className = `notification notification-${type}`;
  notificationEl.style.display = 'block';

  // Auto-hide after 5 seconds
  setTimeout(() => {
    notificationEl.style.display = 'none';
  }, 5000);
}

/**
 * Start auto-refresh of stats
 */
function startAutoRefresh() {
  // Refresh stats every 5 seconds
  setInterval(async () => {
    const auth = await getAuthState();
    if (auth && auth.accessToken) {
      await loadStats();
    }
  }, 5000);
}
