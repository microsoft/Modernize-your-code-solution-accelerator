// AuthService.js
const api = process.env.REACT_APP_API_BASE_URL;// base API URL

// Fetch with JWT Authentication
const fetchWithAuth = async (url: string , method: string = "GET", body: BodyInit | null = null) => {
  const token = localStorage.getItem('token'); // Get the token from localStorage

  const headers: Record<string, string> = {
    'Authorization': `Bearer ${token}`, // Add the token to the Authorization header
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`; // Add the token to the Authorization header
  }

  // If body is FormData, do not set Content-Type header
  if (body && body instanceof FormData) {
    delete headers['Content-Type'];
  } else {
    headers['Content-Type'] = 'application/json';
    body = body ? JSON.stringify(body) : null;
  }

  const options = {
    method,
    headers,
    body: body || undefined,
  };

  try {
    const response = await fetch(`${api}${url}`, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || 'Something went wrong');
    }

    const isJson = response.headers.get('content-type')?.includes('application/json');
    return isJson ? await response.json() : null;
  } catch (error) {
    console.error('API Error:', (error as Error).message);
    throw error;
  }
};

// Vanilla Fetch without Auth for Login
const fetchWithoutAuth = async (url: string , method: string = "POST", body: BodyInit | null = null) => {
  const headers = {
    'Content-Type': 'application/json',
  };

  const options = {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  };

  if (body) {
    options.body = JSON.stringify(body); // Add the body for POST
  }

  try {
    const response = await fetch(`${api}${url}`, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || 'Login failed');
    }

    const isJson = response.headers.get('content-type')?.includes('application/json');
    return isJson ? await response.json() : null;
  } catch (error) {
    console.error('Login Error:', error.message);
    throw error;
  }
};

// Authenticated requests (with token) and login (without token)
export const apiService = {
  get: (url) => fetchWithAuth(url, 'GET'),
  post: (url, body) => fetchWithAuth(url, 'POST', body),
  put: (url, body) => fetchWithAuth(url, 'PUT', body),
  delete: (url) => fetchWithAuth(url, 'DELETE'),
  upload: (url, formData) => fetchWithAuth(url, 'POST', formData),
  login: (url, body) => fetchWithoutAuth(url, 'POST', body), // For login without auth
};

export default apiService;
