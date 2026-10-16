import axios from 'axios';

let rawBaseUrl = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').trim().replace(/\/+$/, '');
const API_BASE_URL = rawBaseUrl.endsWith('/api') ? rawBaseUrl : `${rawBaseUrl}/api`;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('adaptive_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling 401 unauthenticated
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login if session expired
      if (window.location.pathname !== '/login') {
        localStorage.removeItem('adaptive_token');
        localStorage.removeItem('adaptive_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
