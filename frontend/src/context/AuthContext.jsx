/**
 * Auth context — JWT auth state management with Keycloak fallback.
 */
import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};

export const AuthProvider = ({children}) => {
  const [authReady, setAuthReady] = useState(null);  // null = not yet checked
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [perms, setPerms] = useState(null);

  useEffect(() => {
    const saved = localStorage.getItem('mes_user');
    if (saved) {
      try {
        const u = JSON.parse(saved);
        if (u.token) {
          setUser(u);
          setAuthReady(true);
          loadPerms(u.id);
          return;
        }
      } catch {}
    }
    setAuthReady(false);
  }, []);

  const loadPerms = async (userId) => {
    try {
      const r = await api.get(`/api/auth/permissions/${userId}`);
      setPerms(r.data.permissions || []);
    } catch {}
  };

  const login = async (userId, password) => {
    setLoading(true);
    setError('');
    try {
      const r = await api.post('/api/auth/login', {user_id: userId, password});
      if (r.data.error) {
        setError(r.data.error);
        setLoading(false);
        return false;
      }
      const u = {
        id: r.data.user.id,
        name: r.data.user.name,
        role: r.data.user.role,
        token: r.data.token,
      };
      setUser(u);
      localStorage.setItem('mes_user', JSON.stringify(u));
      setAuthReady(true);
      loadPerms(u.id);
      setLoading(false);
      return true;
    } catch (e) {
      setError('Login failed. Check server connection.');
      setLoading(false);
      return false;
    }
  };

  const register = async (formData) => {
    setLoading(true);
    setError('');
    try {
      const r = await api.post('/api/auth/register', formData);
      if (r.data.error) {
        setError(r.data.error);
        setLoading(false);
        return false;
      }
      setError(r.data.message || 'Registration successful! Admin approval required.');
      setLoading(false);
      return true;
    } catch {
      setError('Registration failed.');
      setLoading(false);
      return false;
    }
  };

  const logout = () => {
    setUser(null);
    setPerms(null);
    setAuthReady(false);
    localStorage.removeItem('mes_user');
  };

  const canRead = (menuId) => {
    if (!perms || !user) return true;
    if (user.role === 'admin') return true;
    const p = perms.find(x => x.menu === menuId);
    return p ? p.read : true;
  };

  const canWrite = (menuId) => {
    if (!perms || !user) return false;
    if (user.role === 'admin') return true;
    const p = perms.find(x => x.menu === menuId);
    return p ? p.write : false;
  };

  return (
    <AuthContext.Provider value={{
      authReady, user, loading, error, perms,
      login, register, logout, setError,
      canRead, canWrite,
    }}>
      {children}
    </AuthContext.Provider>
  );
};
