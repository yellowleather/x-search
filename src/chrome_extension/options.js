/**
 * Options Page Logic for X Likes Capture Extension
 * Handles settings configuration and data management
 */

// Initialize options page
document.addEventListener('DOMContentLoaded', async () => {
  await loadSettings();
  await loadStats();
  setupEventHandlers();
});

/**
 * Load current settings and populate form
 */
async function loadSettings() {
  try {
    const settings = await getSettings();

    // Populate form fields
    document.getElementById('backendUrl').value = settings.backendUrl || 'https://api.yourservice.com';
    document.getElementById('captureEnabled').checked = settings.captureEnabled !== false;
    document.getElementById('debugMode').checked = settings.debugMode || false;

  } catch (error) {
    console.error('Error loading settings:', error);
    showError('Failed to load settings');
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

    document.getElementById('queueSize').textContent = `${queueSize} tweet(s)`;
    document.getElementById('totalCaptured').textContent = `${stats.totalCaptured || 0} tweet(s)`;
    document.getElementById('totalSynced').textContent = `${stats.totalSent || 0} tweet(s)`;

  } catch (error) {
    console.error('Error loading stats:', error);
  }
}

/**
 * Setup event handlers for all buttons
 */
function setupEventHandlers() {
  // Save button
  document.getElementById('saveBtn').addEventListener('click', handleSave);

  // Reset button
  document.getElementById('resetBtn').addEventListener('click', handleReset);

  // Test connection button
  document.getElementById('testConnectionBtn').addEventListener('click', handleTestConnection);

  // Export queue button
  document.getElementById('exportQueueBtn').addEventListener('click', handleExportQueue);

  // Clear queue button
  document.getElementById('clearQueueBtn').addEventListener('click', handleClearQueue);
}

/**
 * Handle save settings
 */
async function handleSave() {
  const saveBtn = document.getElementById('saveBtn');

  try {
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';

    // Get form values
    const backendUrl = document.getElementById('backendUrl').value.trim();
    const captureEnabled = document.getElementById('captureEnabled').checked;
    const debugMode = document.getElementById('debugMode').checked;

    // Validate backend URL
    if (!backendUrl) {
      throw new Error('Backend URL is required');
    }

    // Remove trailing slash if present
    const cleanUrl = backendUrl.replace(/\/$/, '');

    // Validate URL format
    try {
      new URL(cleanUrl);
    } catch (e) {
      throw new Error('Invalid URL format');
    }

    // Save settings
    await saveSettings({
      backendUrl: cleanUrl,
      captureEnabled,
      debugMode
    });

    showSuccess('Settings saved successfully!');

  } catch (error) {
    console.error('Error saving settings:', error);
    showError(error.message || 'Failed to save settings');
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = 'Save Settings';
  }
}

/**
 * Handle reset to defaults
 */
async function handleReset() {
  if (!confirm('Are you sure you want to reset all settings to defaults?')) {
    return;
  }

  try {
    // Reset to default settings
    await saveSettings({
      backendUrl: 'https://api.yourservice.com',
      captureEnabled: true,
      debugMode: false
    });

    // Reload settings in form
    await loadSettings();

    showSuccess('Settings reset to defaults');

  } catch (error) {
    console.error('Error resetting settings:', error);
    showError('Failed to reset settings');
  }
}

/**
 * Handle test backend connection
 */
async function handleTestConnection() {
  const testBtn = document.getElementById('testConnectionBtn');
  const statusBox = document.getElementById('connectionStatus');

  try {
    testBtn.disabled = true;
    testBtn.textContent = 'Testing...';

    const backendUrl = document.getElementById('backendUrl').value.trim().replace(/\/$/, '');

    // Validate URL
    if (!backendUrl) {
      throw new Error('Please enter a backend URL');
    }

    // Test health endpoint
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${backendUrl}/api/health`, {
      method: 'GET',
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    statusBox.style.display = 'block';

    if (response.ok) {
      const data = await response.json().catch(() => ({}));

      statusBox.style.borderLeftColor = '#10b981';
      statusBox.innerHTML = `
        <p><strong>✅ Connection successful!</strong></p>
        <p>Backend version: ${data.version || 'Unknown'}</p>
        <p>Status: ${data.status || 'healthy'}</p>
      `;
    } else {
      statusBox.style.borderLeftColor = '#dc2626';
      statusBox.innerHTML = `
        <p><strong>❌ Connection failed</strong></p>
        <p>HTTP Status: ${response.status}</p>
        <p>The backend API is not responding correctly.</p>
      `;
    }

  } catch (error) {
    statusBox.style.display = 'block';
    statusBox.style.borderLeftColor = '#dc2626';

    if (error.name === 'AbortError') {
      statusBox.innerHTML = `
        <p><strong>❌ Connection timeout</strong></p>
        <p>The backend API did not respond within 10 seconds.</p>
      `;
    } else {
      statusBox.innerHTML = `
        <p><strong>❌ Connection failed</strong></p>
        <p>Error: ${error.message}</p>
        <p>Make sure the backend URL is correct and the service is running.</p>
      `;
    }

    console.error('Connection test error:', error);

  } finally {
    testBtn.disabled = false;
    testBtn.textContent = 'Test Connection';
  }
}

/**
 * Handle export queue to JSON file
 */
async function handleExportQueue() {
  try {
    const storage = await chrome.storage.local.get(['queue', 'stats']);
    const queue = storage.queue || [];

    if (queue.length === 0) {
      showError('Queue is empty, nothing to export');
      return;
    }

    // Create export data
    const exportData = {
      exportedAt: new Date().toISOString(),
      queueSize: queue.length,
      stats: storage.stats || {},
      tweets: queue.map(item => ({
        tweetData: item.tweetData,
        queuedAt: new Date(item.queuedAt).toISOString(),
        attempts: item.attempts,
        error: item.error
      }))
    };

    // Create blob and download
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `x-likes-queue-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showSuccess(`Exported ${queue.length} tweet(s) to JSON file`);

  } catch (error) {
    console.error('Error exporting queue:', error);
    showError('Failed to export queue');
  }
}

/**
 * Handle clear queue
 */
async function handleClearQueue() {
  try {
    const storage = await chrome.storage.local.get(['queue']);
    const queue = storage.queue || [];

    if (queue.length === 0) {
      showError('Queue is already empty');
      return;
    }

    const confirmMessage = `Are you sure you want to delete ${queue.length} queued tweet(s)? This cannot be undone.`;

    if (!confirm(confirmMessage)) {
      return;
    }

    // Clear the queue
    await chrome.storage.local.set({ queue: [] });

    // Update stats
    const stats = await getStats();
    stats.queueSize = 0;
    await chrome.storage.local.set({ stats });

    // Reload stats display
    await loadStats();

    showSuccess('Queue cleared successfully');

  } catch (error) {
    console.error('Error clearing queue:', error);
    showError('Failed to clear queue');
  }
}

/**
 * Show success message
 * @param {string} message - Success message
 */
function showSuccess(message) {
  const successEl = document.getElementById('successMessage');
  const errorEl = document.getElementById('errorMessage');

  errorEl.style.display = 'none';
  successEl.textContent = message;
  successEl.style.display = 'block';

  // Auto-hide after 5 seconds
  setTimeout(() => {
    successEl.style.display = 'none';
  }, 5000);

  // Scroll to top to show message
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/**
 * Show error message
 * @param {string} message - Error message
 */
function showError(message) {
  const successEl = document.getElementById('successMessage');
  const errorEl = document.getElementById('errorMessage');

  successEl.style.display = 'none';
  errorEl.textContent = message;
  errorEl.style.display = 'block';

  // Auto-hide after 5 seconds
  setTimeout(() => {
    errorEl.style.display = 'none';
  }, 5000);

  // Scroll to top to show message
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
