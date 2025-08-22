import axios, { AxiosRequestConfig, AxiosRequestHeaders } from 'axios';

export const api = axios.create({ baseURL: 'http://10.0.0.78:8000' });
api.defaults.withCredentials = true;

/* token em cada request */
api.interceptors.request.use(config => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers = {
      ...(config.headers as Record<string, string> | undefined),
      Authorization: `Bearer ${token}`
    } as AxiosRequestHeaders;
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

    const isAuthRoute = original.url?.includes('/auth/login') ||
                        original.url?.includes('/auth/register') ||
                        original.url?.includes('/auth/forgot-password') ||
                        original.url?.includes('/auth/reset-password');

    // Só tenta refresh em rotas que não são de autenticação
    if (error.response?.status === 401 && !original._retry && !isAuthRoute) {
      original._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const { data } = await axios.post('http://10.0.0.78:8000/auth/refresh', {}, { withCredentials: true });
          localStorage.setItem('accessToken', data.access_token);
          queue.forEach(cb => cb(data.access_token));
        } catch (refreshErr) {
          // <<< REFRESH TAMBÉM FALHOU! (exemplo: refresh expirou ou usuário removido)
          localStorage.removeItem('accessToken');
          // redireciona para login (ou faça do jeito que preferir)
          window.location.href = '/login';
          // Rejeita para não tentar de novo
          return Promise.reject(refreshErr);
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
    // <<< SE refresh automático já foi tentado e ainda assim recebeu 401, desloga também
    if (error.response?.status === 401 && original._retry && !isAuthRoute) {
      localStorage.removeItem('accessToken');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // Outras respostas com erro: só repassa
    return Promise.reject(error);
  }
);
