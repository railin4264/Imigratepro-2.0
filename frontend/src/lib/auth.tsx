"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  type AuthUser,
  getMe,
  loadStoredAuthToken,
  login as apiLogin,
  logout as apiLogout,
} from "@/lib/api";

type Status = "loading" | "authenticated" | "unauthenticated";

const AuthContext = createContext<{
  user: AuthUser | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
} | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    const token = loadStoredAuthToken();
    if (!token) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time mount sync, same as LanguageProvider
      setStatus("unauthenticated");
      return;
    }
    getMe()
      .then((me) => {
        setUser(me);
        setStatus("authenticated");
      })
      .catch(() => setStatus("unauthenticated"));
  }, []);

  useEffect(() => {
    // Fired by api.ts's fetchJson whenever a request comes back 401 (expired
    // or revoked token) so every open tab/page reacts, not just the one that
    // happened to make the failing request.
    function handleUnauthorized() {
      setUser(null);
      setStatus("unauthenticated");
    }
    window.addEventListener("migratepro-unauthorized", handleUnauthorized);
    return () => window.removeEventListener("migratepro-unauthorized", handleUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const me = await apiLogin(email, password);
    setUser(me);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setStatus("unauthenticated");
    // Fire-and-forget the server-side revoke -- the UI shouldn't wait on it,
    // logging out locally must always succeed even if the network call fails.
    void apiLogout();
  }, []);

  return <AuthContext.Provider value={{ user, status, login, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
