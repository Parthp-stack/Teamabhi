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
  },

  async forgotPassword(email, role = null) {
    const payload = { email };
    if (role) payload.role = role;
    const response = await api.post('/auth/forgot-password', payload);
    return response.data;
  },

  async verifyResetToken(token) {
    const response = await api.get(`/auth/verify-reset-token?token=${encodeURIComponent(token)}`);
    return response.data;
  },

  async resetPassword(data) {
    // Accepts either { token, new_password, confirm_password } or legacy parameters
    let payload = {};
    if (typeof data === 'string') {
      // Legacy argument signature: resetPassword(email, new_password, otp, role)
      payload = { email: arguments[0], new_password: arguments[1] };
      if (arguments[2]) payload.otp = arguments[2];
      if (arguments[3]) payload.role = arguments[3];
    } else {
      payload = data;
    }
    const response = await api.post('/auth/reset-password', payload);
    return response.data;
  },

  async verifyResetEmail(email, role) {
    const response = await api.post('/auth/verify-reset-email', { email, role });
    return response.data;
  }
};
