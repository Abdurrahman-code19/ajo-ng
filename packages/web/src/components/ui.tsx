import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'md' | 'lg';
  loading?: boolean;
  children: ReactNode;
}

/**
 * THE button. One primary action per screen (DESIGN §6).
 * 40px tall, 8px radius; loading replaces label with a spinner.
 */
export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  children,
  className = '',
  disabled,
  ...rest
}: ButtonProps) {
  const variants: Record<string, string> = {
    primary:
      'bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] active:scale-[0.99]',
    secondary:
      'bg-[var(--surface)] text-[var(--ink)] border border-[var(--line)] hover:border-[var(--primary)] hover:text-[var(--primary)]',
    danger:
      'bg-[var(--danger)] text-white hover:opacity-90',
    ghost:
      'bg-transparent text-[var(--primary)] hover:bg-[var(--primary-wash)]',
  };
  const sizes: Record<string, string> = {
    md: 'h-10 px-4 text-sm',
    lg: 'h-12 px-6 text-base',
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-semibold
        transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-50
        ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <Spinner /> : children}
    </button>
  );
}

export function Spinner({ className = 'h-4 w-4' }: { className?: string }) {
  return (
    <svg className={`animate-spin ${className}`} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  );
}

export function StatusChip({ status }: { status: string }) {
  const map: Record<string, { label: string; dot: string; bg: string; text: string }> = {
    draft: { label: 'Draft', dot: 'bg-[var(--muted)]', bg: 'bg-[var(--cloud)]', text: 'text-[var(--muted)]' },
    enrollment: { label: 'Filling seats', dot: 'bg-[var(--cyan)]', bg: 'bg-[var(--cyan-wash)]', text: 'text-[oklch(40% 0.09 205)]' },
    active: { label: 'Active', dot: 'bg-[var(--success)]', bg: 'bg-[oklch(96% 0.03 155)]', text: 'text-[oklch(40% 0.09 155)]' },
    round_in_progress: { label: 'Round in progress', dot: 'bg-[var(--primary)]', bg: 'bg-[var(--primary-wash)]', text: 'text-[var(--primary)]' },
    completed: { label: 'Completed', dot: 'bg-[var(--primary)]', bg: 'bg-[var(--primary-wash)]', text: 'text-[var(--primary)]' },
    cancelled: { label: 'Cancelled', dot: 'bg-[var(--danger)]', bg: 'bg-[var(--danger-wash)]', text: 'text-[var(--danger)]' },
    cancelling: { label: 'Cancelling', dot: 'bg-[var(--danger)]', bg: 'bg-[var(--danger-wash)]', text: 'text-[var(--danger)]' },
    frozen: { label: 'Frozen', dot: 'bg-[var(--gold)]', bg: 'bg-[var(--gold-wash)]', text: 'text-[oklch(45% 0.1 84)]' },
  };
  const entry = map[status] ?? {
    label: status.replace(/_/g, ' '),
    dot: 'bg-[var(--muted)]',
    bg: 'bg-[var(--cloud)]',
    text: 'text-[var(--muted)]',
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${entry.bg} ${entry.text}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${entry.dot}`} aria-hidden="true" />
      {entry.label}
    </span>
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-[var(--line)] bg-[var(--surface)] ${className}`}>
      {children}
    </div>
  );
}

export function Field({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold">{label}</span>
      {children}
      {hint && !error && <span className="mt-1.5 block text-xs text-[var(--muted)]">{hint}</span>}
      {error && (
        <span className="mt-1.5 block text-xs font-medium text-[var(--danger)]" role="alert">
          {error}
        </span>
      )}
    </label>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={`h-11 w-full rounded-lg border border-[var(--line)] bg-[var(--cloud)] px-3.5 text-base
        placeholder:text-[var(--muted)] transition-colors duration-150
        focus:border-[var(--primary)] focus:bg-[var(--surface)] focus:outline-none
        ${props.className ?? ''}`}
    />
  );
}

export function ErrorBanner({ message }: { message: string | null }) {
  if (!message) {
    return null;
  }
  return (
    <div
      role="alert"
      className="rounded-lg border border-[oklch(80% 0.09 25)] bg-[var(--danger-wash)] px-3.5 py-3 text-sm font-medium text-[var(--danger)]"
    >
      {message}
    </div>
  );
}