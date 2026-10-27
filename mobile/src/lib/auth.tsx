import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { api, setSession, type Membership, type Tokens } from "./api";
import { TENANT_SLUG } from "./config";
import { storage } from "./storage";

type Session = { email: string; memberships: Membership[] };
type AuthResponse = Tokens & { memberships: Membership[] };

type AuthContextValue = {
  /** null: sin sesión. */
  session: Session | null;
  /** true mientras se restaura la sesión guardada al abrir la app. */
  loading: boolean;
  /** Dueño o staff de este negocio: ve el modo personal (pedidos y caja). */
  isStaff: boolean;
  /** Solo el dueño: puede además encender o apagar promociones. */
  isOwner: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: { email: string; password: string; full_name?: string; phone?: string }) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth fuera de AuthProvider");
  return value;
}

const TOKENS_KEY = "tokens";
const SESSION_KEY = "session";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSessionState] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  const clear = useCallback(async () => {
    setSession(null);
    setSessionState(null);
    await Promise.all([storage.remove(TOKENS_KEY), storage.remove(SESSION_KEY)]);
  }, []);

  const persist = useCallback(async (email: string, data: AuthResponse) => {
    const tokens = { access: data.access, refresh: data.refresh };
    setSession(tokens);
    const next = { email, memberships: data.memberships };
    setSessionState(next);
    await Promise.all([
      storage.set(TOKENS_KEY, JSON.stringify(tokens)),
      storage.set(SESSION_KEY, JSON.stringify(next)),
    ]);
  }, []);

  useEffect(() => {
    // Cuando el cliente renueva el token (o lo invalida) se refleja aquí.
    const listener = (tokens: Tokens | null) => {
      if (tokens) storage.set(TOKENS_KEY, JSON.stringify(tokens)).catch(() => {});
      else clear().catch(() => {});
    };
    (async () => {
      try {
        const [savedTokens, savedSession] = await Promise.all([
          storage.get(TOKENS_KEY),
          storage.get(SESSION_KEY),
        ]);
        if (savedTokens && savedSession) {
          setSession(JSON.parse(savedTokens), listener);
          setSessionState(JSON.parse(savedSession));
        } else {
          setSession(null, listener);
        }
      } catch {
        setSession(null, listener);
      } finally {
        setLoading(false);
      }
    })();
  }, [clear]);

  const login = useCallback(
    async (email: string, password: string) => {
      const normalized = email.trim().toLowerCase();
      let data = await api<AuthResponse>("/api/auth/login/", {
        method: "POST",
        body: { email: normalized, password },
        auth: false,
      });
      // Cuenta que ya existe en otro negocio: se une a este con la misma contraseña.
      if (!data.memberships.some((m) => m.tenant === TENANT_SLUG)) {
        data = await api<AuthResponse>("/api/auth/register/", {
          method: "POST",
          body: { tenant: TENANT_SLUG, email: normalized, password },
          auth: false,
        });
      }
      await persist(normalized, data);
    },
    [persist],
  );

  const register = useCallback(
    async (form: { email: string; password: string; full_name?: string; phone?: string }) => {
      const email = form.email.trim().toLowerCase();
      const data = await api<AuthResponse>("/api/auth/register/", {
        method: "POST",
        body: { ...form, email, tenant: TENANT_SLUG },
        auth: false,
      });
      await persist(email, data);
    },
    [persist],
  );

  const value = useMemo(() => {
    const role = session?.memberships.find((m) => m.tenant === TENANT_SLUG)?.role;
    return { session, loading, isStaff: role === "owner" || role === "staff", isOwner: role === "owner", login, register, logout: clear };
  }, [session, loading, login, register, clear]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
