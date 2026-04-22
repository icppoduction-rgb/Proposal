import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import type { TokenPair, User } from "../types/api";

interface AuthContextValue {
  user: User | null;
  tokens: TokenPair | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<string | null>;
  ensureAccessToken: (minRemainingSeconds?: number) => Promise<string | null>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const STORAGE_KEY = "cybersec-platform-auth";
const ACCESS_TOKEN_REFRESH_THRESHOLD_SECONDS = 120;

function parseJwtExpiration(token: string): number | null {
  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  const encodedPayload = parts[1].replace(/-/g, "+").replace(/_/g, "/");
  const paddedPayload = encodedPayload.padEnd(Math.ceil(encodedPayload.length / 4) * 4, "=");

  try {
    if (typeof atob !== "function") {
      return null;
    }
    const payload = JSON.parse(atob(paddedPayload)) as { exp?: unknown };
    return typeof payload.exp === "number" ? payload.exp : null;
  } catch {
    return null;
  }
}

function shouldRefreshAccessToken(token: string, minRemainingSeconds: number): boolean {
  const expiration = parseJwtExpiration(token);
  if (expiration === null) {
    return false;
  }
  return Date.now() + minRemainingSeconds * 1000 >= expiration * 1000;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [tokens, setTokens] = useState<TokenPair | null>(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? (JSON.parse(stored) as TokenPair) : null;
  });
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const refreshPromiseRef = useRef<Promise<TokenPair | null> | null>(null);

  const persistTokens = useCallback((next: TokenPair) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    setTokens(next);
  }, []);

  const clearAuthState = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
    setTokens(null);
    setUser(null);
  }, []);

  const refreshTokenPair = useCallback(async () => {
    if (!tokens) {
      return null;
    }
    if (refreshPromiseRef.current) {
      return refreshPromiseRef.current;
    }

    const pendingRefresh = api
      .refresh(tokens.refresh_token)
      .then((next) => {
        persistTokens(next);
        return next;
      })
      .catch((error) => {
        clearAuthState();
        throw error;
      })
      .finally(() => {
        refreshPromiseRef.current = null;
      });

    refreshPromiseRef.current = pendingRefresh;
    return pendingRefresh;
  }, [clearAuthState, persistTokens, tokens]);

  useEffect(() => {
    if (!tokens) {
      setUser(null);
      setLoading(false);
      return;
    }
    api.me(tokens.access_token)
      .then(setUser)
      .catch(async () => {
        try {
          const next = await refreshTokenPair();
          if (!next) {
            setUser(null);
            return;
          }
          const refreshedUser = await api.me(next.access_token);
          setUser(refreshedUser);
        } catch {
          clearAuthState();
        }
      })
      .finally(() => setLoading(false));
  }, [clearAuthState, refreshTokenPair, tokens]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      tokens,
      loading,
      async login(email: string, password: string) {
        const tokenPair = await api.login(email, password);
        persistTokens(tokenPair);
      },
      async logout() {
        try {
          if (tokens) {
            await api.logout(tokens.refresh_token);
          }
        } finally {
          clearAuthState();
        }
      },
      async refresh() {
        const next = await refreshTokenPair();
        return next?.access_token ?? null;
      },
      async ensureAccessToken(minRemainingSeconds = ACCESS_TOKEN_REFRESH_THRESHOLD_SECONDS) {
        if (!tokens) {
          return null;
        }
        if (!shouldRefreshAccessToken(tokens.access_token, minRemainingSeconds)) {
          return tokens.access_token;
        }
        const next = await refreshTokenPair();
        return next?.access_token ?? null;
      },
    }),
    [clearAuthState, loading, persistTokens, refreshTokenPair, tokens, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
