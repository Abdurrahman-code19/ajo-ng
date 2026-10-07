import { useState, type ReactNode } from 'react';
import { Bell, Home, LogOut, Plus, ReceiptText, WalletCards, X } from 'lucide-react';
import { useAuth } from '../auth';
import { Avatar } from './ui';

type SheetKind = 'bell' | 'profile' | null;

/**
 * The responsive app chrome (wireframe §2, §3, §5):
 *  - desktop (lg+): navy sidebar with brand, nav and the signed-in card;
 *  - mobile: frosted top bar + the fixed bottom tray (Home · Create · Bell · Me);
 *  - bell/profile open as bottom sheets (mobile) or dialogs (desktop).
 */
export function AppShell({ children }: { children: ReactNode }) {
  const { view, navigate } = useAuth();
  const [sheet, setSheet] = useState<SheetKind>(null);

  const title =
    view.kind === 'create' ? 'Create an Ajo' : view.kind === 'ajo' ? 'Ajo overview' : 'My Ajos';

  const navItem = (active: boolean, soon = false) =>
    `flex h-10 items-center gap-3 rounded-xl px-3 text-sm font-medium transition-colors duration-150 ${
      active
        ? 'bg-white/15 text-white'
        : soon
          ? 'cursor-not-allowed text-white/35'
          : 'text-white/70 hover:bg-white/10 hover:text-white'
    }`;

  return (
    <div className="min-h-screen bg-[var(--cloud)]">
      {/* Desktop sidebar */}
      <aside className="bg-gradient-navy fixed inset-y-0 left-0 z-40 hidden w-72 flex-col px-5 py-6 text-white lg:flex">
        <button
          type="button"
          onClick={() => navigate({ kind: 'dashboard' })}
          className="flex w-fit items-center gap-2.5"
          aria-label="AJO.ng — home"
        >
          <img src="/ajo-mark.png" alt="AJO.ng" className="h-9 w-auto" />
        </button>

        <nav className="mt-10 flex flex-col gap-1" aria-label="Primary">
          <button
            type="button"
            onClick={() => navigate({ kind: 'dashboard' })}
            className={navItem(view.kind === 'dashboard')}
          >
            <Home className="h-[18px] w-[18px]" aria-hidden="true" />
            Dashboard
          </button>
          <button
            type="button"
            onClick={() => navigate({ kind: 'create' })}
            className={navItem(view.kind === 'create')}
          >
            <Plus className="h-[18px] w-[18px]" aria-hidden="true" />
            Create an Ajo
          </button>
          <button type="button" onClick={() => setSheet('bell')} className={navItem(false)}>
            <Bell className="h-[18px] w-[18px]" aria-hidden="true" />
            Notifications
          </button>

          <p className="mt-6 px-3 pb-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-white/40">
            Coming with payments
          </p>
          <span className={navItem(false, true)} title="Arrives with the payments provider">
            <WalletCards className="h-[18px] w-[18px]" aria-hidden="true" />
            Payments
            <span className="ml-auto rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-white/45">
              soon
            </span>
          </span>
          <span className={navItem(false, true)} title="Arrives with the payments provider">
            <ReceiptText className="h-[18px] w-[18px]" aria-hidden="true" />
            Activity &amp; ledger
            <span className="ml-auto rounded-full bg-white/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-white/45">
              soon
            </span>
          </span>
        </nav>

        <UserCard className="mt-auto" />
      </aside>

      {/* Top bar */}
      <header className="glass sticky top-0 z-30 border-b border-[var(--line)] lg:pl-72">
        <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-2">
            <img src="/ajo-mark.png" alt="AJO.ng" className="h-8 w-auto lg:hidden" />
            <h1 className="font-display hidden text-lg font-semibold text-[var(--ink)] lg:block">
              {title}
            </h1>
          </div>
          <button
            type="button"
            onClick={() => setSheet('bell')}
            className="relative flex h-9 w-9 items-center justify-center rounded-xl text-[var(--muted)] transition-colors hover:bg-[var(--cloud)] hover:text-[var(--ink)]"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" aria-hidden="true" />
            <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-[var(--gold)]" aria-hidden="true" />
          </button>
        </div>
      </header>

      {/* Page */}
      <div className="lg:pl-72">
        <main className="mx-auto w-full max-w-5xl px-4 pb-28 pt-6 sm:px-6 lg:px-8 lg:pb-16 lg:pt-8">
          {children}
        </main>
      </div>

      {/* Mobile bottom tray */}
      <nav
        className="glass safe-bottom fixed inset-x-0 bottom-0 z-40 border-t border-[var(--line)] lg:hidden"
        aria-label="Primary"
      >
        <div className="flex h-16 items-stretch px-2">
          <button
            type="button"
            onClick={() => navigate({ kind: 'dashboard' })}
            className={`flex flex-1 flex-col items-center justify-center gap-1 text-[11px] font-medium ${
              view.kind === 'dashboard' ? 'text-[var(--primary)]' : 'text-[var(--muted)]'
            }`}
          >
            <Home className="h-5 w-5" aria-hidden="true" />
            Home
          </button>

          <button
            type="button"
            onClick={() => navigate({ kind: 'create' })}
            aria-label="Create an Ajo"
            className="flex flex-1 items-center justify-center"
          >
            <span className="bg-gradient-cta -translate-y-3 flex h-12 w-12 items-center justify-center rounded-2xl text-white shadow-[0_10px_24px_-8px_var(--primary)] transition-transform active:scale-95">
              <Plus className="h-6 w-6" aria-hidden="true" />
            </span>
          </button>

          <button
            type="button"
            onClick={() => setSheet('bell')}
            className={`flex flex-1 flex-col items-center justify-center gap-1 text-[11px] font-medium ${
              sheet === 'bell' ? 'text-[var(--primary)]' : 'text-[var(--muted)]'
            }`}
          >
            <Bell className="h-5 w-5" aria-hidden="true" />
            Alerts
          </button>

          <button
            type="button"
            onClick={() => setSheet('profile')}
            className={`flex flex-1 flex-col items-center justify-center gap-1 text-[11px] font-medium ${
              sheet === 'profile' ? 'text-[var(--primary)]' : 'text-[var(--muted)]'
            }`}
          >
            <Avatar name="Member" size="sm" />
            Me
          </button>
        </div>
      </nav>

      {sheet !== null && <Sheet kind={sheet} onClose={() => setSheet(null)} />}
    </div>
  );
}

function UserCard({ className = '' }: { className?: string }) {
  const { user, logout } = useAuth();
  const name = user?.email ?? 'Signed out';
  return (
    <div className={`flex items-center gap-3 rounded-2xl bg-white/5 p-3 ${className}`}>
      <Avatar name={name} size="md" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-white">{name.split('@')[0]}</p>
        <p className="truncate text-xs text-white/50">{user?.email}</p>
      </div>
      <button
        type="button"
        onClick={logout}
        aria-label="Sign out"
        className="flex h-9 w-9 items-center justify-center rounded-xl text-white/50 transition-colors hover:bg-white/10 hover:text-white"
      >
        <LogOut className="h-[18px] w-[18px]" aria-hidden="true" />
      </button>
    </div>
  );
}

function Sheet({ kind, onClose }: { kind: 'bell' | 'profile'; onClose: () => void }) {
  const { user, logout } = useAuth();
  const name = user?.email ?? 'Signed out';
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-[var(--deep)]/50 backdrop-blur-sm sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="anim-pop w-full max-w-md rounded-t-3xl border border-[var(--line)] bg-[var(--surface)] p-6 shadow-[var(--shadow-pop)] sm:rounded-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold text-[var(--ink)]">
            {kind === 'bell' ? 'Notifications' : 'Your profile'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted)] transition-colors hover:bg-[var(--cloud)] hover:text-[var(--ink)]"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {kind === 'bell' ? (
          <div className="mt-6 py-4 text-center">
            <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--primary-wash)] text-[var(--primary)]">
              <Bell className="h-6 w-6" aria-hidden="true" />
            </span>
            <p className="mt-4 text-sm font-semibold text-[var(--ink)]">Nothing here yet</p>
            <p className="mx-auto mt-1 max-w-xs text-sm leading-relaxed text-[var(--muted)]">
              Invites, collection notices and payment reminders land here — the moment the
              backend sends one. This demo reads from a live API, so nothing is invented.
            </p>
          </div>
        ) : (
          <div className="mt-6">
            <div className="flex items-center gap-3 rounded-2xl border border-[var(--line)] p-4">
              <Avatar name={name} size="lg" />
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-[var(--ink)]">{user?.email}</p>
                <p className="text-xs text-[var(--muted)]">{user ? 'Verified member' : 'Not signed in'}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              className="mt-3 flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-[var(--line)] text-sm font-semibold text-[var(--danger)] transition-colors hover:border-[var(--danger)]"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              Sign out
            </button>
          </div>
        )}
      </div>
    </div>
  );
}