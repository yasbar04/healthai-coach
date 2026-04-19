import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { login as apiLogin, me as apiMe } from "../api/auth";
import { getErrorMessage } from "../api/client";
import type { User } from "../types";

type AuthState = {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  clearError: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem("healthai_token"));
  const [user, setUser] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refreshMe() {
    if (!token) { 
      setUser(null); 
      setIsLoading(false); 
      return; 
    }
    try {
      const u = await apiMe();
      setUser(u);
      setError(null);
    } catch (err) {
      const msg = getErrorMessage(err);
      setError(msg);
      setUser(null);
      localStorage.removeItem("healthai_token");
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => { refreshMe(); }, [token]);

  const value = useMemo<AuthState>(() => ({
    token,
    user,
    isLoading,
    error,
    login: async (email, password) => {
      try {
        const res = await apiLogin(email.trim(), password);
        const t = res.access_token;
        localStorage.setItem("healthai_token", t);
        setToken(t);
        setError(null);
      } catch (err) {
        const msg = getErrorMessage(err);
        setError(msg);
        throw err;
      }
    },
    logout: () => {
      localStorage.removeItem("healthai_token");
      setToken(null);
      setUser(null);
      setError(null);
    },
    clearError: () => setError(null)
  }), [token, user, isLoading, error]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
