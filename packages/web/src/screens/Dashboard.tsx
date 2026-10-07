import { useCallback, useEffect, useState } from 'react';
import { ArrowRight, CalendarDays, CircleDollarSign, Plus, RotateCw } from 'lucide-react';
import { api, dayLabel, frequencyLabel, naira } from '../api';
import type { AjoSummary } from '../api-types';
import { useAuth } from '../auth';
import { TopBar } from '../components/TopBar';
import { Button, Card, ErrorBanner, Spinner, StatusChip } from '../components/ui';

export function Dashboard() {
  const { navigate } = useAuth();
  const [ajos, setAjos] = useState<AjoSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const result = await api.listAjos();
      // Live clients will poll; the demo re-fetches on focus so the partner can
      // watch a seat fill in another tab and come back to a fresh rail.
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

  const live = ajos?.filter((ajo) => ajo.status === 'enrollment' || ajo.status === 'active') ?? [];
  const rest = ajos?.filter((ajo) => !(ajo.status === 'enrollment' || ajo.status === 'active')) ?? [];

  return (
    <div className="min-h-screen bg-[var(--cloud)]">
      <TopBar onHome={() => navigate({ kind: 'dashboard' })} />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold tracking-tight">My Ajos</h1>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Everything you belong to — what is due next is always at the top.
            </p>
          </div>
          <button
            type="button"
            onClick={() => void refresh()}
            className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-[var(--line)] bg-[var(--surface)] px-3 text-sm font-semibold text-[var(--ink)] transition-colors hover:border-[var(--primary)] hover:text-[var(--primary)]"
          >
            <RotateCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} aria-hidden="true" />
            Refresh
          </button>
        </div>

        {error && <div className="mt-6"><ErrorBanner message={error} /></div>}

        {ajos === null ? (
          <div className="flex h-64 items-center justify-center">
            <Spinner className="h-6 w-6 text-[var(--primary)]" />
          </div>
        ) : ajos.length === 0 ? (
          <EmptyState onCreate={() => navigate({ kind: 'create' })} />
        ) : (
          <>
            {live.length > 0 && (
              <section className="mt-8">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                  Needs you now
                </p>
                <div className="grid gap-4 sm:grid-cols-2">
                  {live.map((ajo) => (
                    <AjoCardBody key={ajo.id} ajo={ajo} onOpen={() => navigate({ kind: 'ajo', id: ajo.id })} primary />
                  ))}
                </div>
              </section>
            )}

            {rest.length > 0 && (
              <section className="mt-10">
                <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
                  Your Ajos
                </p>
                <div className="grid gap-4 sm:grid-cols-2">
                  {rest.map((ajo) => (
                    <AjoCardBody key={ajo.id} ajo={ajo} onOpen={() => navigate({ kind: 'ajo', id: ajo.id })} />
                  ))}
                </div>
              </section>
            )}
          </>
        )}

        <section className="mt-12 rounded-2xl border border-dashed border-[var(--line)] bg-[var(--surface)] p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Start a group with people you trust</h2>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Five to twenty of you. Fixed contributions. Everybody takes a turn.
              </p>
            </div>
            <Button onClick={() => navigate({ kind: 'create' })}>
              <Plus className="h-4 w-4" aria-hidden="true" /> Create an Ajo
            </Button>
          </div>
        </section>
      </main>
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
    <Card className={`overflow-hidden ${primary ? 'sm:col-span-2' : ''}`}>
      <button
        type="button"
        onClick={onOpen}
        className="block w-full p-5 text-left transition-colors hover:bg-[oklch(98% 0.005 255)]"
        aria-label={`Open ${ajo.name}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-xs font-medium text-[var(--muted)]">{ajo.reference}</p>
            <h3 className="mt-0.5 truncate text-lg font-semibold tracking-tight">{ajo.name}</h3>
          </div>
          <StatusChip status={ajo.status} />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-[var(--ink)]">
          <span className="tnum inline-flex items-center gap-1.5 font-semibold">
            <CircleDollarSign className="h-4 w-4 text-[var(--gold)]" aria-hidden="true" />
            {naira(ajo.contributionKobo)}
            <span className="font-normal text-[var(--muted)]">
              {frequencyLabel(ajo.frequency)}
            </span>
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
                  className={`h-2 flex-1 rounded-full ${i < ajo.positionsFilled ? 'bg-[var(--cyan)]' : 'bg-[var(--cloud)]'}`}
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
    <div className="mt-10">
      <Card className="p-10 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--primary-wash)] text-[var(--primary)]">
          <Plus className="h-8 w-8" aria-hidden="true" />
        </div>
        <h2 className="mt-5 text-xl font-semibold tracking-tight">Start your first Ajo</h2>
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