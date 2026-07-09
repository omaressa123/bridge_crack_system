export const API_URL = 'http://localhost:8000';

export async function authenticatedFetch(url, options = {}) {
  const token = localStorage.getItem('token');
  
  // Set headers
  const headers = {
    ...options.headers,
  };
  
  // Don't set Content-Type if uploading a file via FormData (let browser set it with boundary)
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = headers['Content-Type'] || 'application/json';
  }
  
  // Set JWT Token
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // Handle unauthorized (session expired/invalid)
  if (response.status === 401) {
    console.warn('Unauthorized or expired session. Logging out.');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.reload();
  }
  
  return response;
}
