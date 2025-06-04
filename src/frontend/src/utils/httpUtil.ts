// AuthService.ts

import { getApiUrl } from "./config";

let api:string;//import.meta.env.VITE_API_URL; // Replace with your API URL
// Define the types for the response
interface ApiResponse<T = any> {
  data: T;
}

interface FetchOptions {
  method: string;
  headers: HeadersInit;
  body?: string | FormData | null;
}

export const updateUrl=()=>{
  api = getApiUrl() ?? ''; // Provide a fallback empty string if getApiUrl() returns null
}

// Fetch with JWT Authentication
const fetchWithAuth = async <T>(url: string, method: string = 'GET', body: any): Promise<T | null> => {
  const token = localStorage.getItem('token'); // Get the token from localStorage

  const headers: HeadersInit = {
    'Authorization': `Bearer ${token}`, // Add the token to the Authorization header
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Cache-Control': 'no-cache',
  };

  // If body is FormData, do not set Content-Type header
  if (body instanceof FormData) {
    delete headers['Content-Type'];
  } else {
    headers['Content-Type'] = 'application/json';
    body = body ? JSON.stringify(body) : null;
  }

  const options: FetchOptions = {
    method,
    headers,
  };

  if (body) {
    options.body = body; // Add the body only if it exists (for POST, PUT)
  }

  try {
    const response = await fetch(`${api}${url}`, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || 'Something went wrong');
    }

    const isJson = response.headers.get('content-type')?.includes('application/json');
    return isJson ? (await response.json()) as T : null;
  } catch (error: any) {
    //console.error('API Error:', error.message);
    throw error;
  }
};

// Fetch with JWT Authentication
const fetchHeadersWithAuth = async <T>(url: string, method: string = 'GET', body: any = null): Promise<any> => {
  const token = localStorage.getItem('token'); // Get the token from localStorage

  const headers: HeadersInit = {
    'Authorization': `Bearer ${token}`, // Add the token to the Authorization header
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Cache-Control': 'no-cache',
  };

  // If body is FormData, do not set Content-Type header
  if (body instanceof FormData) {
    delete headers['Content-Type'];
  } else {
    headers['Content-Type'] = 'application/json';
    body = body ? JSON.stringify(body) : null;
  }

  const options: FetchOptions = {
    method,
    headers,
  };

  if (body) {
    options.body = body; // Add the body only if it exists (for POST, PUT)
  }

  try {
    const response = await fetch(`${api}${url}`, options);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || 'Something went wrong');
    }
    return response;

  } catch (error: any) {
    //console.error('API Error:', error.message);
    throw error;
  }
};

// Vanilla Fetch without Auth for Login
const fetchWithoutAuth = async <T>(url: string, method: string = 'POST', body: any = null): Promise<T | null> => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  const options: FetchOptions = {
    method,
    headers,
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
    return isJson ? (await response.json()) as T : null;
  } catch (error: any) {
    //console.error('Login Error:', error.message);
    throw error;
  }
};

// Authenticated requests (with token) and login (without token)
export const httpUtility = {
  get: <T>(url: string): Promise<T | null> => fetchWithAuth<T>(url, 'GET', null),
  post: <T>(url: string, body: any): Promise<T | null> => fetchWithAuth<T>(url, 'POST', body),
  put: <T>(url: string, body: any): Promise<T | null> => fetchWithAuth<T>(url, 'PUT', body),
  delete: <T>(url: string): Promise<T | null> => fetchWithAuth<T>(url, 'DELETE', null),
  upload: <T>(url: string, formData: FormData): Promise<T | null> => fetchWithAuth<T>(url, 'POST', formData),
  login: <T>(url: string, body: any): Promise<T | null> => fetchWithoutAuth<T>(url, 'POST', body), // For login without auth
  headers : <T>(url: string): Promise<any> => fetchHeadersWithAuth<T>(url, 'GET'),  
};

export default httpUtility;
