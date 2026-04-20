const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Simple cache for GET requests (companies, operateurs, etc.)
const requestCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

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
 * Shared API helper with automatic 401 handling, token refresh retry, and caching for GET.
 * On 401, attempts one token refresh before retrying the original request.
 * GET requests are cached for 5 minutes to reduce server load.
 *
 * @param {string} url - API endpoint (without base URL)
 * @param {object} options - fetch options (method, headers, body)
 * @param {number} timeoutMs - timeout in milliseconds (default: 150000 for long operations)
 * @returns {Promise<Response>} - fetch response
 */
export async function apiFetch(url, options = {}, timeoutMs = 150000) {
  const method = (options.method || 'GET').toUpperCase();
  
  // Check cache for GET requests
  if (method === 'GET') {
    const cached = requestCache.get(url);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      console.log(`[Cache HIT] ${url}`);
      return cached.response.clone();
    }
  }

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

  // Create AbortController for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    let response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      signal: controller.signal,
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
          signal: controller.signal,
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

    // Cache successful GET responses
    if (method === 'GET' && response.ok) {
      requestCache.set(url, {
        response: response.clone(),
        timestamp: Date.now()
      });
    }

    return response;
  } catch (error) {
    if (error.name === 'AbortError') {
      throw new Error(`Timeout: La génération de convocation a pris trop de temps (>${timeoutMs / 1000}s). Veuillez réessayer.`);
    }
    throw error;
  } finally {
    clearTimeout(timeoutId);
  }
}

/**
 * Clear request cache (call after mutations)
 */
export function clearCache() {
  requestCache.clear();
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
