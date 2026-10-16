import api from './api';

export const authService = {
  async login(email, password) {
    const response = await api.post('/auth/login', { email, password });
    if (response.data.access_token) {
      localStorage.setItem('adaptive_token', response.data.access_token);
      localStorage.setItem('adaptive_user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  async register(name, email, password, role = 'STUDENT') {
    const response = await api.post('/auth/register', { name, email, password, role });
    if (response.data.access_token) {
      localStorage.setItem('adaptive_token', response.data.access_token);
      localStorage.setItem('adaptive_user', JSON.stringify(response.data.user));
    }
    return response.data;
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('adaptive_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  getToken() {
    return localStorage.getItem('adaptive_token');
  },

  logout() {
    localStorage.removeItem('adaptive_token');
    localStorage.removeItem('adaptive_user');
    window.location.href = '/login';
  },

  async getMe() {
    const response = await api.get('/auth/me');
    localStorage.setItem('adaptive_user', JSON.stringify(response.data));
    return response.data;
  }
};
