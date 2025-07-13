import axios from 'axios';

const API_BASE_URL = 'http://10.0.2.2:5000/api'; // Android emulator
// const API_BASE_URL = 'http://localhost:5000/api'; // iOS simulator

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

export const authAPI = {
  login: async (username, password) => {
    const response = await api.post('/login', {username, password});
    return response.data;
  },
};

export const chamaAPI = {
  getDashboard: async () => {
    const response = await api.get('/dashboard');
    return response.data;
  },

  contribute: async (amount, phone, description) => {
    const response = await api.post('/contribute', {
      amount,
      phone,
      description,
    });
    return response.data;
  },

  getLoans: async () => {
    const response = await api.get('/loans');
    return response.data;
  },

  getDiscussions: async () => {
    const response = await api.get('/discussions');
    return response.data;
  },

  getActivities: async () => {
    const response = await api.get('/activities');
    return response.data;
  },
};

export default api;