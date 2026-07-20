"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { type AuthUser, getMe, login as apiLogin, logout as apiLogout } from "@/lib/api";

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
    // No token to inspect client-side anymore (it's an httpOnly cookie) --
    // the only way to know if there's a valid session is to ask the server.
    // The browser attaches the cookie automatically if it has one; if there
    // isn't one (or it's expired/revoked), this 401s and we land on "unauthenticated".
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
