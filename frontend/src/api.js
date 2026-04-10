const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * Refresh the JWT token automatically.
 * Returns the new token or throws if refresh fails.
 */
export async function refreshToken() {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('NO_SESSION');
  }

  const response = await fetch(`${API_BASE_URL}/api/refresh`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!response.ok) {
    localStorage.removeItem('token');
    throw new Error('SESSION_EXPIRED');
  }

  const data = await response.json();
  localStorage.setItem('token', data.token);
  return data.token;
}

/**
 * Shared API helper with automatic 401 handling and token refresh retry.
 * On 401, attempts one token refresh before retrying the original request.
 *
 * @param {string} url - API endpoint (without base URL)
 * @param {object} options - fetch options (method, headers, body)
 * @returns {Promise<Response>} - fetch response
 */
export async function apiFetch(url, options = {}) {
  let token = localStorage.getItem('token');

  if (!token) {
    throw new Error('SESSION_EXPIRED');
  }

  const defaultHeaders = {
    'Authorization': `Bearer ${token}`
  };

  // Auto-add Content-Type for JSON bodies
  if (options.body && typeof options.body === 'string') {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  let response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers
    }
  });

  if (response.status === 401) {
    // Try to refresh the token once
    try {
      const newToken = await refreshToken();
      // Retry the original request with the new token
      response = await fetch(`${API_BASE_URL}${url}`, {
        ...options,
        headers: {
          'Authorization': `Bearer ${newToken}`,
          ...options.headers
        }
      });

      if (response.status === 401) {
        // Refresh succeeded but still 401 — session truly invalid
        localStorage.removeItem('token');
        throw new Error('SESSION_EXPIRED');
      }
    } catch (refreshErr) {
      if (refreshErr.message === 'SESSION_EXPIRED') {
        throw refreshErr;
      }
      // Network error during refresh
      localStorage.removeItem('token');
      throw new Error('SESSION_EXPIRED');
    }
  }

  return response;
}

/**
 * Helper for handling API responses consistently.
 * Throws error message on non-OK responses.
 * 
 * @param {Response} response - fetch response
 * @returns {Promise<object>} - parsed JSON data
 */
export async function handleResponse(response) {
  // Check if response is JSON before parsing
  const contentType = response.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    console.error(`[API] Expected JSON response but got: ${contentType}`);
    console.error(`[API] URL: ${response.url}`);
    console.error(`[API] Status: ${response.status} ${response.statusText}`);

    // Try to read the body for debugging
    const text = await response.text().catch(() => '');
    if (text.startsWith('<!') || text.startsWith('<html')) {
      throw new Error('Le serveur a retourné une page HTML au lieu de JSON. Vérifiez que le backend est démarré sur http://localhost:5000');
    }
    throw new Error(`Réponse inattendue du serveur (${response.status})`);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.error || `Erreur serveur (${response.status})`);
  }
  return response.json();
}

export { API_BASE_URL };
