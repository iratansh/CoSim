import { createContext, ReactNode, useEffect, useMemo, useState } from 'react';

import { me } from '../api/auth';
import type { User } from '../api/types';

export interface AuthContextValue {
  token: string | null;
  user: User | null;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const TOKEN_STORAGE_KEY = 'cosim-token';

interface Props {
  children: ReactNode;
}

export const AuthProvider = ({ children }: Props) => {
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_STORAGE_KEY);
  });
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
      me(token)
        .then(setUser)
        .catch((error) => {
          // Silently handle 401 errors (invalid/expired token)
          if (error.response?.status === 401) {
            console.warn('Token expired or invalid, logging out');
            setToken(null);
          } else {
            console.error('Failed to fetch user:', error);
          }
          setUser(null);
        });
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
      setUser(null);
    }
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      user,
      login: setToken,
      logout: () => {
        setUser(null);
        setToken(null);
      }
    }),
    [token, user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
