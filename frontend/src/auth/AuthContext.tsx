import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, ApiError } from "../api/client";
import type { User } from "../types";

type RegisterInput = { name: string; email: string; age: number; password: string };
type AuthValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => void;
};

const TOKEN_KEY = "nexus_access_token";
const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    setLoading(true);
    api.me(token)
      .then((currentUser) => active && setUser(currentUser))
      .catch((error: unknown) => {
        if (!active) return;
        if (error instanceof ApiError && error.status === 401) {
          localStorage.removeItem(TOKEN_KEY);
          setToken(null);
        }
        setUser(null);
      })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [token]);

  async function login(email: string, password: string) {
    const result = await api.login(email, password);
    localStorage.setItem(TOKEN_KEY, result.access_token);
    setToken(result.access_token);
  }

  async function register(input: RegisterInput) {
    await api.register(input);
    await login(input.email, input.password);
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
    window.location.hash = "#/dashboard";
  }

  const value = useMemo(() => ({ user, token, loading, login, register, logout }), [user, token, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
