/**
 * The lifecycle rail — DESIGN §5, the one thing the app is remembered for.
 *
 * The Ajo's state machine rendered literally as nodes on a track. The enrollment
 * moment rides on it: ten seat pips, a window countdown, and when the last seat
 * fills the rail physically advances (the `advancing` prop drives a 420ms draw).
 */
import { useEffect, useState } from 'react';
import { dayLabel, frequencyLabel, naira } from '../api';
import type { AjoSummary } from '../api-types';

const STEPS = [
  { key: 'draft', label: 'Draft' },
  { key: 'enrollment', label: 'Filling seats' },
  { key: 'active', label: 'Active' },
  { key: 'round_in_progress', label: 'Round in progress' },
  { key: 'completed', label: 'Completed' },
] as const;

function stepIndex(status: string): number {
  if (status === 'cancelled' || status === 'cancelling' || status === 'frozen') {
    return -1;
  }
  const found = STEPS.findIndex((step) => step.key === status);
  return found === -1 ? 0 : found;
}

function secondsUntil(target: string | null): number | null {
  if (target === null) {
    return null;
  }
  const ms = new Date(target).getTime() - Date.now();
  return ms > 0 ? ms : 0;
}

function formatWindow(totalRemainingMs: number | null): string {
  if (totalRemainingMs === null) {
    return '—';
  }
  const total = Math.max(0, Math.ceil(totalRemainingMs / 1000));
  const days = Math.floor(total / 86400);
  const hours = Math.floor((total % 86400) / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  if (days > 0) {
    return `${days}d ${hours}h`;
  }
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

export function LifecycleRail({
  ajo,
  advancing = false,
  onTick,
}: {
  ajo: AjoSummary;
  /** True while the enrollment→active transition is animating. */
  advancing?: boolean;
  /** Called every second while in enrollment, so the parent can poll. */
  onTick?: () => void;
}) {
  const status = ajo.status;
  const index = stepIndex(status);
  const [remaining, setRemaining] = useState<number | null>(
    secondsUntil(ajo.enrollmentClosesAt),
  );

  useEffect(() => {
    if (status !== 'enrollment') {
      setRemaining(null);
      return;
    }
    const tick = () => {
      const next = secondsUntil(ajo.enrollmentClosesAt);
      setRemaining(next);
      // Every minute rather than every tick — a finance UI does not animate
      // seconds (DESIGN §7). But the parent poll on the 60s boundary.
      if (next !== null && next % 60 === 0) {
        onTick?.();
      }
    };
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, [status, ajo.enrollmentClosesAt, onTick]);

  const fullFiveDays = 5 * 24 * 60 * 60 * 1000;
  const windowTotal =
    ajo.enrollmentOpensAt === null || ajo.enrollmentClosesAt === null
      ? fullFiveDays
      : Math.max(
          fullFiveDays,
          new Date(ajo.enrollmentClosesAt).getTime() -
            new Date(ajo.enrollmentOpensAt).getTime(),
        );
  const drain =
    remaining === null ? 100 : Math.max(0, Math.min(100, (remaining / windowTotal) * 100));
  const urgent = remaining !== null && remaining < 24 * 60 * 60 * 1000;
  const seatsFilled = ajo.positionsFilled;

  return (
    <section
      aria-label={`${ajo.name}, status ${ajo.status}`}
      className="relative overflow-hidden rounded-2xl bg-[var(--deep)] text-white"
    >
      <div className="relative z-10 p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-4">
          <div>
            <p className="text-xs font-medium tracking-wide text-white/55">
              {ajo.reference}
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight sm:text-3xl">
              {ajo.name}
            </h1>
          </div>

          {status === 'enrollment' ? (
            <div className="text-right" aria-live="off">
              <p className="text-xs font-medium tracking-wide text-[var(--cyan)]">
                Window closes in
              </p>
              <p
                className={`tnum mt-0.5 text-3xl font-semibold sm:text-4xl ${
                  urgent ? 'text-[var(--gold)]' : 'text-white'
                }`}
              >
                {formatWindow(remaining)}
              </p>
            </div>
          ) : (
            <div className="text-right">
              <p className="text-xs font-medium tracking-wide text-white/55">Contribution</p>
              <p className={`tnum mt-0.5 text-2xl font-semibold text-[var(--gold)]`}>
                {naira(ajo.contributionKobo)}
              </p>
              <p className="text-xs text-white/55">
                {frequencyLabel(ajo.frequency)} · {dayLabel(ajo.collectionDay)}
              </p>
            </div>
          )}
        </div>

        {/* The track */}
        <ol
          className="mt-8 flex items-center"
          aria-label="Lifecycle"
          aria-current={index >= 0 ? `step` : undefined}
        >
          {STEPS.map((step, i) => {
            const reached = i <= index;
            const current = i === index;
            const trailing = i === STEPS.length - 1;
            return (
              <li key={step.key} className={`flex items-center ${trailing ? '' : 'flex-1'}`}>
                <Node
                  label={step.label}
                  reached={reached}
                  current={current}
                  isLast={trailing}
                />
                {!trailing && <TrackFilled filled={i < index} advancing={advancing} />}
              </li>
            );
          })}
        </ol>

        {/* Seat ticker + pips */}
        {(status === 'enrollment' || status === 'active' || status === 'draft') && (
          <div className="mt-8 flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="tnum text-4xl font-semibold tracking-tight">
                {seatsFilled}
                <span className="text-2xl text-white/45"> / {ajo.positionsTotal}</span>
              </p>
              <p className="mt-1 text-sm text-white/60">
                {status === 'enrollment'
                  ? seatsFilled < ajo.positionsTotal
                    ? 'seats claimed — fills the moment all are taken'
                    : 'last seat claimed — activating…'
                  : 'seats filled'}
              </p>
            </div>
            <div className="flex gap-1.5" aria-label={`${seatsFilled} of ${ajo.positionsTotal} seats filled`}>
              {Array.from({ length: ajo.positionsTotal }, (_, i) => (
                <span
                  key={i}
                  className={`h-2.5 rounded-full transition-colors duration-200 ${
                    i < seatsFilled ? 'bg-[var(--cyan)]' : 'bg-white/20'
                  }`}
                  style={{ width: `${Math.max(6, 100 / ajo.positionsTotal) * 0.55}rem` }}
                  aria-hidden="true"
                />
              ))}
            </div>
          </div>
        )}

        {/* Window drain line */}
        {status === 'enrollment' && (
          <div
            className="absolute bottom-0 left-0 h-1.5 w-full bg-white/10"
            role="presentation"
          >
            <div
              className={`h-full transition-[width] duration-500 ${urgent ? 'bg-[var(--gold)]' : 'bg-[var(--cyan)]'}`}
              style={{ width: `${drain}%` }}
            />
          </div>
        )}
      </div>
    </section>
  );
}

function Node({
  label,
  reached,
  current,
  isLast,
}: {
  label: string;
  reached: boolean;
  current: boolean;
  isLast: boolean;
}) {
  return (
    <div className="relative flex flex-col items-center gap-1.5">
      <span
        className={`flex items-center justify-center rounded-full transition-colors duration-200 ${
          reached ? 'bg-white' : 'bg-white/20'
        } ${current ? 'ring-2 ring-[var(--cyan)] ring-offset-2 ring-offset-[var(--deep)] h-3.5 w-3.5' : 'h-2.5 w-2.5'}`}
        aria-hidden="true"
      />
      <span
        className={`whitespace-nowrap text-xs font-semibold ${
          current ? 'text-white' : reached ? 'text-white/70' : 'text-white/40'
        } ${isLast ? 'hidden sm:block' : ''}`}
        aria-hidden={current ? 'false' : 'true'}
      >
        {label}
      </span>
    </div>
  );
}

function TrackFilled({ filled, advancing }: { filled: boolean; advancing: boolean }) {
  return (
    <div
      className={`h-0.5 flex-1 mx-1.5 sm:mx-3 ${filled ? 'bg-white' : 'bg-white/20'}`}
      style={{
        transition: advancing ? 'background-color 420ms cubic-bezier(0.2,0.8,0.2,1)' : undefined,
      }}
      aria-hidden="true"
    />
  );
}