import { LogOut, Plus } from 'lucide-react';
import { useAuth } from '../auth';

/**
 * The 56px sticky topbar. Desktop: mark on the left, actions on the right.
 * The logo on light surfaces is the warmer "Primary" mark from brand/.
 */
export function TopBar({ onHome }: { onHome: () => void }) {
  const { user, logout, navigate } = useAuth();
  const initials =
    user === null
      ? '?'
      : user.email
          .split('@')[0]
          .slice(0, 2)
          .toUpperCase();

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--line)] bg-[var(--surface)]/95 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4 sm:px-6">
        <button
          type="button"
          onClick={onHome}
          className="flex items-center gap-2"
          aria-label="AJO.ng — home"
        >
          <img src="/ajo-mark.png" alt="AJO.ng" className="h-9 w-auto" />
        </button>

        <nav className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate({ kind: 'create' })}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-[var(--primary)] px-3 text-sm font-semibold text-white transition-colors hover:bg-[var(--primary-hover)]"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Create Ajo
          </button>
          <span className="ml-1 flex items-center gap-2" title={user?.email ?? ''}>
            <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--primary-wash)] text-xs font-bold text-[var(--primary)]">
              {initials}
            </span>
            <button
              type="button"
              onClick={logout}
              title="Sign out"
              aria-label="Sign out"
              className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted)] transition-colors hover:bg-[var(--cloud)] hover:text-[var(--ink)]"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
            </button>
          </span>
        </nav>
      </div>
    </header>
  );
}