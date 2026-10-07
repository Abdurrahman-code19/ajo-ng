import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, CalendarDays, CircleDollarSign, Plus, RotateCw, Sparkles } from 'lucide-react';
import { api, dayLabel, frequencyLabel, naira } from '../api';
import type { AjoSummary } from '../api-types';
import { useAuth } from '../auth';
import { useCountUp } from '../hooks/useCountUp';
import { Avatar, Button, Card, ErrorBanner, Skeleton, StatusChip } from '../components/ui';

export function Dashboard() {
  const { navigate, user } = useAuth();
  const [ajos, setAjos] = useState<AjoSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const result = await api.listAjos();
      setAjos(result.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load your Ajos.');
    }
  }, []);

  useEffect(() => {
    void load();
    const onFocus = () => void load();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [load]);

  async function refresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  const list = ajos ?? [];
  const live = list.filter((ajo) => ajo.status === 'enrollment' || ajo.status === 'active');
  const rest = list.filter((ajo) => !(ajo.status === 'enrollment' || ajo.status === 'active'));

  const monthlyNaira = Math.round(
    list.reduce((sum, ajo) => {
      const kobo = ajo.contributionKobo ?? 0;
      if (ajo.frequency === 'WEEKLY') return sum + kobo * 4.3333;
      if (ajo.frequency === 'BIWEEKLY') return sum + kobo * 2.1667;
      return sum + kobo; // monthly
    }, 0) / 100,
  );
  const seatsFilled = list.reduce((sum, ajo) => sum + ajo.positionsFilled, 0);
  const seatsTotal = list.reduce((sum, ajo) => sum + ajo.positionsTotal, 0);

  // Count-up targets are stable numbers, so the hooks' call order never changes.
  const liveCount = useCountUp(live.length);
  const seatsFilledCount = useCountUp(seatsFilled);
  const monthlyCount = useCountUp(monthlyNaira);

  const loading = ajos === null;
  const firstName =
    (user?.email.split('@')[0] ?? 'there').replace(/[._-]/g, ' ').trim().split(/\s+/)[0] ?? 'there';

  return (
    <div>
      {error && (
        <div className="mb-6">
          <ErrorBanner message={error} />
        </div>
      )}

      <Hero firstName={firstName} ajoCount={list.length} monthlyNaira={monthlyNaira} />

      {/* Summary strip */}
      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        {loading ? (
          <>
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
            <Skeleton className="h-24" />
          </>
        ) : (
          <>
            <SummaryCard
              className="anim-fade-up"
              icon={<CircleDollarSign className="h-5 w-5" />}
              label="Monthly commitment"
              value={`₦${monthlyCount.toLocaleString('en-NG')}`}
              sub={list.length === 0 ? 'nothing scheduled yet' : 'fixed across your Ajos'}
            />
            <SummaryCard
              className="anim-fade-up anim-delay-1"
              icon={<Sparkles className="h-5 w-5" />}
              label="Live right now"
              value={String(liveCount)}
              sub="active or filling seats"
            />
            <SummaryCard
              className="anim-fade-up anim-delay-2"
              icon={<UsersMark />}
              label="Seats claimed"
              value={`${seatsFilledCount}/${seatsTotal}`}
              sub="of your seats filled"
            />
          </>
        )}
      </div>

      {loading ? (
        <ListSkeleton />
      ) : list.length === 0 ? (
        <EmptyState onCreate={() => navigate({ kind: 'create' })} />
      ) : (
        <>
          {live.length > 0 && (
            <section className="mt-8">
              <SectionHeader
                eyebrow="Needs you now"
                action={
                  <button
                    type="button"
                    onClick={() => void refresh()}
                    className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-[var(--line)] bg-[var(--surface)] px-3 text-sm font-semibold text-[var(--ink)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)]"
                  >
                    <RotateCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
                    Refresh
                  </button>
                }
              />
              <div className="grid gap-4 sm:grid-cols-2">
                {live.map((ajo, i) => (
                  <div key={ajo.id} className={`anim-fade-up anim-delay-${Math.min(i + 1, 4)}`}>
                    <AjoCardBody ajo={ajo} onOpen={() => navigate({ kind: 'ajo', id: ajo.id })} primary />
                  </div>
                ))}
              </div>
            </section>
          )}

          {rest.length > 0 && (
            <section className="mt-10">
              <SectionHeader eyebrow="Your Ajos" />
              <div className="grid gap-4 sm:grid-cols-2">
                {rest.map((ajo) => (
                  <AjoCardBody key={ajo.id} ajo={ajo} onOpen={() => navigate({ kind: 'ajo', id: ajo.id })} />
                ))}
              </div>
            </section>
          )}
        </>
      )}

      <SectionCTA onCreate={() => navigate({ kind: 'create' })} />
    </div>
  );
}

function Hero({
  firstName,
  ajoCount,
  monthlyNaira,
}: {
  firstName: string;
  ajoCount: number;
  monthlyNaira: number;
}) {
  const now = new Date();
  const hour = now.getHours();
  const period = hour < 12 ? 'morning' : hour < 17 ? 'afternoon' : 'evening';
  const month = useCountUp(monthlyNaira);
  const dateLine = now.toLocaleDateString('en-NG', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  });

  return (
    <section className="bg-gradient-navy relative overflow-hidden rounded-3xl p-6 text-white sm:p-8">
      <div className="glow-blob -right-16 -top-20 h-72 w-72 bg-[var(--primary)]/45" />
      <div
        className="glow-blob -bottom-24 left-1/4 h-64 w-64 bg-[var(--cyan)]/30"
        style={{ animationDelay: '0.8s' }}
      />
      <div className="relative z-10 flex flex-wrap items-end justify-between gap-x-8 gap-y-6">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-white/50">{dateLine}</p>
          <h1 className="font-display mt-2 text-3xl font-bold sm:text-4xl">
            Good {period}, <span className="text-gradient-cyan">{nameCase(firstName)}</span>
          </h1>
          <p className="mt-2 max-w-md text-sm leading-relaxed text-white/65">
            {ajoCount === 0
              ? 'Everything you save starts with one Ajo. Set the rules, invite the group, and let the turn-taking begin.'
              : `You belong to ${ajoCount} ${ajoCount === 1 ? 'Ajo' : 'Ajos'}. What is due to you is always at the top.`}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-white/50">
            Your monthly commitment
          </p>
          <p className="tnum font-display mt-1 text-4xl font-bold sm:text-5xl">
            ₦{month.toLocaleString('en-NG')}
          </p>
          <p className="mt-1 text-xs text-white/55">
            {ajoCount === 0 ? 'nothing scheduled yet' : `across ${ajoCount} Ajos · fixed each cycle`}
          </p>
        </div>
      </div>
    </section>
  );
}

function SummaryCard({
  icon,
  label,
  value,
  sub,
  className = '',
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
  className?: string;
}) {
  return (
    <Card className={`flex items-center gap-4 p-4 ${className}`}>
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[var(--primary-wash)] text-[var(--primary)]">
        {icon}
      </span>
      <div className="min-w-0">
        <p className="text-xs font-semibold text-[var(--muted)]">{label}</p>
        <p className="tnum font-display mt-0.5 text-xl font-bold leading-none text-[var(--ink)]">{value}</p>
        <p className="mt-1 truncate text-xs text-[var(--muted)]">{sub}</p>
      </div>
    </Card>
  );
}

function SectionHeader({ eyebrow, action }: { eyebrow: string; action?: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <p className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">{eyebrow}</p>
      {action}
    </div>
  );
}

export function AjoCardBody({
  ajo,
  onOpen,
  primary = false,
}: {
  ajo: AjoSummary;
  onOpen: () => void;
  primary?: boolean;
}) {
  return (
    <Card
      className={`overflow-hidden transition-transform duration-200 hover:-translate-y-0.5 ${
        primary ? 'sm:col-span-2' : ''
      }`}
    >
      <button
        type="button"
        onClick={onOpen}
        className="block w-full p-5 text-left transition-colors hover:bg-[oklch(99% 0.004 255)]"
        aria-label={`Open ${ajo.name}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-[var(--muted)]">{ajo.reference}</p>
            <h3 className="font-display mt-0.5 truncate text-lg font-semibold tracking-tight">{ajo.name}</h3>
          </div>
          <StatusChip status={ajo.status} />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-[var(--ink)]">
          <span className="tnum inline-flex items-center gap-1.5 font-semibold">
            <CircleDollarSign className="h-4 w-4 text-[var(--gold)]" aria-hidden="true" />
            {naira(ajo.contributionKobo)}
            <span className="font-normal text-[var(--muted)]">{frequencyLabel(ajo.frequency)}</span>
          </span>
          <span className="inline-flex items-center gap-1.5 text-[var(--muted)]">
            <CalendarDays className="h-4 w-4" aria-hidden="true" />
            {dayLabel(ajo.collectionDay)}
          </span>
          <span className="tnum text-[var(--muted)]">
            your seat {ajo.yourPosition ?? '—'} of {ajo.positionsTotal}
          </span>
        </div>

        {ajo.status === 'enrollment' && (
          <div className="mt-4">
            <div className="flex gap-1.5" aria-hidden="true">
              {Array.from({ length: ajo.positionsTotal }, (_, i) => (
                <span
                  key={i}
                  className={`h-2 flex-1 rounded-full transition-colors duration-300 ${
                    i < ajo.positionsFilled ? 'bg-gradient-cta' : 'bg-[var(--cloud)]'
                  }`}
                />
              ))}
            </div>
            <div className="mt-2 flex items-center justify-between text-xs">
              <span className="tnum font-semibold text-[var(--muted)]">
                {ajo.positionsFilled}/{ajo.positionsTotal} seats
              </span>
              <span className="inline-flex items-center gap-1 font-semibold text-[var(--primary)]">
                Open the Ajo <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </span>
            </div>
          </div>
        )}
      </button>
    </Card>
  );
}

function EmptyState({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="anim-pop mt-8">
      <Card className="p-10 text-center">
        <Avatar name="AJO.ng" size="lg" className="mx-auto rounded-2xl" />
        <h2 className="font-display mt-5 text-xl font-semibold tracking-tight">Start your first Ajo</h2>
        <p className="mx-auto mt-2 max-w-sm text-sm leading-relaxed text-[var(--muted)]">
          A group of 5–20 saves together, taking turns collecting the full pool.
          You set the rules, invite the group, and everybody pays on schedule.
        </p>
        <div className="mt-6">
          <Button onClick={onCreate} size="lg">
            Create an Ajo
          </Button>
        </div>
      </Card>
    </div>
  );
}

function SectionCTA({ onCreate }: { onCreate: () => void }) {
  return (
    <section className="mt-12 rounded-2xl border border-dashed border-[var(--line)] bg-[var(--surface)] p-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="font-display text-lg font-semibold">Start a group with people you trust</h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Five to twenty of you. Fixed contributions. Everybody takes a turn.
          </p>
        </div>
        <Button onClick={onCreate}>
          <Plus className="h-4 w-4" aria-hidden="true" /> Create an Ajo
        </Button>
      </div>
    </section>
  );
}

function ListSkeleton() {
  return (
    <div>
      <Skeleton className="mt-10 h-6 w-40" />
      <div className="mt-3 grid gap-4 sm:grid-cols-2">
        <Skeleton className="h-44" />
        <Skeleton className="h-44" />
      </div>
    </div>
  );
}

function nameCase(name: string): string {
  return name.charAt(0).toUpperCase() + name.slice(1);
}

function UsersMark() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <circle cx="9" cy="8" r="3.2" />
      <path d="M3.5 19c.6-3.2 2.7-5 5.5-5s4.9 1.8 5.5 5" />
      <circle cx="16.5" cy="9" r="2.4" />
      <path d="M16 14.2c2.7.2 4.4 1.8 4.9 4.3" />
    </svg>
  );
}