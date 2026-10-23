import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginApi, registerApi } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('rag_token') || '');
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('rag_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = async (email, password) => {
    const data = await loginApi(email, password);
    setToken(data.access_token);
    setUser({ id: data.user_id, email: data.email });
    localStorage.setItem('rag_token', data.access_token);
    localStorage.setItem('rag_user', JSON.stringify({ id: data.user_id, email: data.email }));
    return data;
  };

  const register = async (email, password) => {
    const data = await registerApi(email, password);
    if (data.access_token) {
      setToken(data.access_token);
      setUser({ id: data.user_id, email: data.email });
      localStorage.setItem('rag_token', data.access_token);
      localStorage.setItem('rag_user', JSON.stringify({ id: data.user_id, email: data.email }));
    }
    return data;
  };

  const logout = () => {
    setToken('');
    setUser(null);
    localStorage.removeItem('rag_token');
    localStorage.removeItem('rag_user');
  };

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated: !!token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de un AuthProvider');
  }
  return context;
}
