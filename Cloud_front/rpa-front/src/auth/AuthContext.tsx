import React, { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../services/api';

interface AuthData {
  user: string | null;
  token: string | null;
  login: (u: string, p: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthData>({} as AuthData);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser]   = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('accessToken'));

  /* 1) extrai usuário quando já existe token em localStorage */
  useEffect(() => {
    if (token) {
      const payload = JSON.parse(atob(token.split('.')[1]));
      setUser(payload.sub);
    }
  }, [token]);

  /* 2) login */
  async function login(username: string, password: string) {
    const form = new URLSearchParams();
    form.append('username', username);
    form.append('password', password);

    /* --------- AQUI: withCredentials --------- */
    const res = await api.post('/auth/login', form, { withCredentials: true });

    setToken(res.data.access_token);
    localStorage.setItem('accessToken', res.data.access_token);
  }

  /* 3) logout */
  function logout() {
    setToken(null);
    setUser(null);
    localStorage.removeItem('accessToken');
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  return useContext(AuthContext);
}
