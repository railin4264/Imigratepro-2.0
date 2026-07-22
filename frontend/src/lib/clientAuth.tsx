"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import {
  type AuthenticatedClient,
  getClientMe,
  clientLogin as apiClientLogin,
  clientLogout as apiClientLogout,
} from "@/lib/api";

type Status = "loading" | "authenticated" | "unauthenticated";

const ClientAuthContext = createContext<{
  client: AuthenticatedClient | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
} | null>(null);

export function ClientAuthProvider({ children }: { children: React.ReactNode }) {
  const [client, setClient] = useState<AuthenticatedClient | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    getClientMe()
      .then((me) => {
        setClient(me);
        setStatus("authenticated");
      })
      .catch(() => setStatus("unauthenticated"));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const me = await apiClientLogin(email, password);
    setClient(me);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(() => {
    setClient(null);
    setStatus("unauthenticated");
    void apiClientLogout();
  }, []);

  return <ClientAuthContext.Provider value={{ client, status, login, logout }}>{children}</ClientAuthContext.Provider>;
}

export function useClientAuth() {
  const ctx = useContext(ClientAuthContext);
  if (!ctx) throw new Error("useClientAuth must be used within ClientAuthProvider");
  return ctx;
}
