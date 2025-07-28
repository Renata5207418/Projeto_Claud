import axios, { AxiosRequestConfig, AxiosRequestHeaders } from 'axios';

export const api = axios.create({ baseURL: 'http://localhost:8000' });
api.defaults.withCredentials = true;

/* token em cada request */
api.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers = {
      ...(config.headers as Record<string, string> | undefined),
      Authorization: `Bearer ${token}`
    } as AxiosRequestHeaders;                   // ← cast único, sem erro
  }
  return config;
});

/* refresh automático se 401 */
let isRefreshing = false;
let queue: Array<(t: string) => void> = [];

api.interceptors.response.use(
  res => res,
  async error => {
    const original: AxiosRequestConfig & { _retry?: boolean } = error.config;

    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const { data } = await axios.post('http://localhost:8000/auth/refresh', {}, { withCredentials: true });
          localStorage.setItem('accessToken', data.access_token);
          queue.forEach(cb => cb(data.access_token));
        } finally {
          isRefreshing = false;
          queue = [];
        }
      }

      return new Promise((resolve, reject) => {
        queue.push(token => {
          if (!token) return reject(error);
          original.headers = {
            ...(original.headers as Record<string, string> | undefined),
            Authorization: `Bearer ${token}`
          } as AxiosRequestHeaders;
          resolve(axios(original));
        });
      });
    }
    return Promise.reject(error);
  }
);
