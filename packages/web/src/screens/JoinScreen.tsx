import { useCallback, useEffect, useState } from 'react';
import { Check, CircleDollarSign, ShieldCheck, X } from 'lucide-react';
import { api, ApiError, frequencyLabel } from '../api';
import type { InvitationPreview } from '../api-types';
import { useAuth } from '../auth';
import { TopBar } from '../components/TopBar';
import { Button, Card, ErrorBanner, Spinner } from '../components/ui';

function dayLabel(day: string | null): string {
  if (day === null) {
    return '—';
  }
  return day.charAt(0) + day.slice(1).toLowerCase();
}

/**
 * The invitee-facing screen, reached from a shared invite link.
 *
 * The preview is anonymous — seeing what you are being asked to commit to is
 * the last thing that should require an account. Accepting does require the
 * signed-in member whose email matches the invitation; the screen says so.
 */
export function JoinScreen({ token }: { token: string }) {
  const { user, navigate } = useAuth();
  const [preview, setPreview] = useState<InvitationPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ positionNumber: number; ajoId: string } | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setPreview(await api.previewInvite(token));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'The invitation could not be read.');
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function accept() {
    setError(null);
    setBusy(true);
    try {
      const accepted = await api.acceptInvite(token);
      setResult({ positionNumber: accepted.positionNumber, ajoId: accepted.ajoId });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not accept the invitation.');
    } finally {
      setBusy(false);
    }
  }

  async function decline() {
    setError(null);
    setBusy(true);
    try {
      await api.declineInvite(token);
    } catch {
      // The invitation is gone either way from this screen's point of view.
    } finally {
      setBusy(false);
      navigate({ kind: 'dashboard' });
    }
  }

  if (preview === null) {
    return (
      <div className="min-h-screen bg-[var(--cloud)]">
        <TopBar onHome={() => navigate({ kind: 'dashboard' })} />
        <main className="mx-auto max-w-xl px-4 py-10 sm:px-6">
          {error !== null && <ErrorBanner message={error} />}
          {error === null && (
            <div className="flex h-64 items-center justify-center">
              <Spinner className="h-7 w-7 text-[var(--primary)]" />
            </div>
          )}
        </main>
      </div>
    );
  }

  const { ajo } = preview;
  const seatsFilled = ajo.membersCount ?? 0;
  const seatsTotal = ajo.maxMembers;
  const contribution = preview.feeDisclosure;

  if (result !== null) {
    return (
      <div className="min-h-screen bg-[var(--cloud)]">
        <TopBar onHome={() => navigate({ kind: 'dashboard' })} />
        <main className="mx-auto max-w-xl px-4 py-10 sm:px-6">
          <Card className="p-8 text-center">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[oklch(96% 0.03 155)] text-[var(--success)]">
              <Check className="h-8 w-8" aria-hidden="true" />
            </div>
            <h1 className="mt-5 text-2xl font-semibold tracking-tight">You're in</h1>
            <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
              You hold seat <strong className="tnum text-[var(--ink)]">{result.positionNumber}</strong> in{' '}
              <strong className="text-[var(--ink)]">{ajo.name}</strong>.
              {seatsFilled >= seatsTotal
                ? ' You were the last seat — the Ajo has activated by itself.'
                : ' The Ajo activates when the last seat is filled.'}
            </p>
            <div className="mt-6">
              <Button onClick={() => navigate({ kind: 'ajo', id: result.ajoId })} size="lg" className="w-full">
                See your Ajo
              </Button>
            </div>
          </Card>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--cloud)]">
      <TopBar onHome={() => navigate({ kind: 'dashboard' })} />
      <main className="mx-auto max-w-xl px-4 py-10 sm:px-6">
        <Card className="overflow-hidden">
          <div className="bg-[var(--deep)] px-6 py-8 text-white sm:px-8">
            <p className="text-xs font-medium uppercase tracking-wider text-white/55">
              {preview.organizer.name} invited you to
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight">{ajo.name}</h1>
            <div className="mt-6 grid grid-cols-3 gap-4">
              <Fact label="Contribution" value={`₦${(contribution.contributionKobo / 100).toLocaleString('en-NG')}`} sub={frequencyLabel(ajo.frequencyCode as never)} />
              <Fact label="Collection day" value={dayLabel(ajo.collectionDay)} sub={`${ajo.durationRounds} rounds`} />
              <Fact label="Seats" value={`${seatsFilled}/${seatsTotal}`} sub={seatsFilled >= seatsTotal ? 'about to fill' : 'still open'} />
            </div>
            <div className="mt-6 rounded-xl bg-white/10 p-4">
              <p className="flex items-center gap-2 text-sm text-white/70">
                <CircleDollarSign className="h-4 w-4 text-[var(--gold)]" aria-hidden="true" />
                You pay ₦{(contribution.totalChargeKobo / 100).toLocaleString('en-NG')} per round
                — that's your ₦{(contribution.contributionKobo / 100).toLocaleString('en-NG')} contribution plus a
                ₦{(contribution.feeKobo / 100).toLocaleString('en-NG')} service fee. The fee never touches what the
                pool pays out.
              </p>
            </div>
          </div>

          <div className="px-6 py-6 sm:px-8">
            <h2 className="text-base font-semibold">What you're agreeing to</h2>
            <ul className="mt-3 space-y-2.5 text-sm leading-relaxed text-[var(--ink)]">
              {preview.rules.clauses.map((rule) => (
                <li key={rule.code} className="flex gap-2.5">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-[var(--success)]" aria-hidden="true" />
                  <span>{rule.text}</span>
                </li>
              ))}
            </ul>

            <div className="mt-6">
              <ErrorBanner message={error} />
            </div>

            {user === null ? (
              <div className="mt-4">
                <p className="mb-3 text-center text-sm text-[var(--muted)]">
                  The invitation is tied to the email it was sent to. Sign in with that account to accept.
                </p>
                <Button onClick={() => navigate({ kind: 'auth' })} className="w-full" size="lg">
                  Sign in to accept
                </Button>
              </div>
            ) : (
              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Button onClick={() => void accept()} loading={busy} className="flex-1" size="lg">
                  <Check className="h-4 w-4" aria-hidden="true" /> I accept — take the seat
                </Button>
                <Button variant="secondary" onClick={() => void decline()} className="sm:shrink-0" size="lg">
                  <X className="h-4 w-4" aria-hidden="true" /> Decline
                </Button>
              </div>
            )}
          </div>
        </Card>
      </main>
    </div>
  );
}

function Fact({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div>
      <p className="text-xs font-medium text-white/55">{label}</p>
      <p className="tnum mt-1 text-xl font-semibold">{value}</p>
      <p className="mt-0.5 text-xs text-white/55">{sub}</p>
    </div>
  );
}