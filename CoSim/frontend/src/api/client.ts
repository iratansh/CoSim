import axios from 'axios';

const defaultBase = '/api';
const envBase = import.meta.env.VITE_API_BASE_URL;
const baseURL = (envBase ? envBase.replace(/\/$/, '') : defaultBase);

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const authorizedClient = (token: string | null) => {
  const instance = axios.create({
    baseURL,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (token) {
    instance.interceptors.request.use(config => {
      config.headers = config.headers ?? {};
      config.headers.Authorization = `Bearer ${token}`;
      return config;
    });
  }

  return instance;
};
