import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { api, setToken, type AuthResponse } from './api';

export type View =
  | { kind: 'auth' }
  | { kind: 'dashboard' }
  | { kind: 'create' }
  | { kind: 'ajo'; id: string }
  | { kind: 'join'; token: string };

interface AuthContextValue {
  user: { id: string; email: string } | null;
  view: View;
  navigate: (view: View) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
  booting: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** Boot-time view from the URL, so shared invite links (/join/:token) open the invite. */
function viewFromPath(): View {
  const match = /^\/join\/([A-Za-z0-9_-]+)\/?$/.exec(window.location.pathname);
  if (match) {
    return { kind: 'join', token: match[1] };
  }
  return { kind: 'auth' };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<{ id: string; email: string } | null>(null);
  const [booting, setBooting] = useState(true);
  const [view, setView] = useState<View>(viewFromPath);

  const refresh = useCallback(async () => {
    if (window.localStorage.getItem('ajo.web.accessToken') === null) {
      setBooting(false);
      return;
    }
    try {
      const me = await api.me();
      setUser({ id: me.userId, email: me.email });
      setView((current) => (current.kind === 'auth' ? { kind: 'dashboard' } : current));
    } catch {
      setToken(null);
    } finally {
      setBooting(false);
    }
  }, []);

  const navigate = useCallback((next: View) => {
    setView(next);
    window.scrollTo({ top: 0 });
  }, []);

const login = useCallback(async (email: string, password: string) => {
    const session: AuthResponse = await api.login(email, password);
    setToken(session.accessToken);
    const me = await api.me();
    setUser({ id: me.userId, email: me.email });
    // An invitee signed in from /join/:token should land back on the invite.
    const match = /^\/join\/([A-Za-z0-9_-]+)\/?$/.exec(window.location.pathname);
    setView(match ? { kind: 'join', token: match[1] } : { kind: 'dashboard' });
  }, []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setView({ kind: 'auth' });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, view, navigate, login, logout, refresh, booting }),
    [user, view, navigate, login, logout, refresh, booting],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (value === null) {
    throw new Error('useAuth must be used inside <AuthProvider>');
  }
  return value;
}