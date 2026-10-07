import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowLeft, Copy, Crown, Link2, UserPlus } from 'lucide-react';
import { api, ApiError, dayLabel, frequencyLabel, naira } from '../api';
import type { AjoDetail as AjoDetailData } from '../api-types';
import { useAuth } from '../auth';
import { TopBar } from '../components/TopBar';
import { Button, Card, ErrorBanner, Field, Input, Spinner, StatusChip } from '../components/ui';
import { LifecycleRail } from '../components/LifecycleRail';

export function AjoDetail({ id }: { id: string }) {
  const { navigate } = useAuth();
  const [detail, setDetail] = useState<AjoDetailData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [full, setFull] = useState(false);
  const [inviteOpen, setInviteOpen] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      const result = await api.getAjo(id);
      setDetail(result);
      setFull(result.ajo.positionsFilled >= result.ajo.positionsTotal);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not load the Ajo.');
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  // Poll while in enrollment, so the rail advances the moment the last seat
  // fills — that is the demo's whole argument (DESIGN §5).
  useEffect(() => {
    if (detail?.ajo.status !== 'enrollment') {
      return;
    }
    const idHandle = window.setInterval(() => {
      void load();
    }, 4000);
    return () => window.clearInterval(idHandle);
  }, [detail?.ajo.status, load]);

  if (detail === null) {
    return (
      <div className="min-h-screen bg-[var(--cloud)]">
        <TopBar onHome={() => navigate({ kind: 'dashboard' })} />
        <div className="flex h-96 items-center justify-center">
          {error ? <ErrorBanner message={error} /> : <Spinner className="h-7 w-7 text-[var(--primary)]" />}
        </div>
      </div>
    );
  }

  const { ajo, positions, members } = detail;
  const isOrganizer = ajo.yourRole === 'organizer';
  const showSeats = ajo.status === 'enrollment' || ajo.status === 'draft';

  return (
    <div className="min-h-screen bg-[var(--cloud)]">
      <TopBar onHome={() => navigate({ kind: 'dashboard' })} />
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">
        <button
          type="button"
          onClick={() => navigate({ kind: 'dashboard' })}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--muted)] transition-colors hover:text-[var(--primary)]"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to My Ajos
        </button>

        {error && <div className="mt-6"><ErrorBanner message={error} /></div>}

        <div className="mt-4">
          <LifecycleRail ajo={ajo} advancing={full} onTick={() => void load()} />
        </div>

        {/* The seat board — DISCRETE seats (DESIGN §4), not a progress bar. */}
        {showSeats && (
          <section className="mt-8" aria-label="Seat board">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold tracking-tight">
                The seats
                <span className="ml-2 text-sm font-normal text-[var(--muted)]">
                  {full ? 'the group filled itself' : `${positions.length - (full ? positions.length : ajo.positionsFilled)} left to fill`}
                </span>
              </h2>
              <StatusChip status={ajo.status} />
            </div>
            <Card className="p-5 sm:p-6">
              <div className="grid grid-cols-5 gap-2.5 sm:grid-cols-10">
                {positions.map((seat) => (
                  <div
                    key={seat.positionNumber}
                    className={`relative flex aspect-square items-center justify-center rounded-xl border transition-colors duration-200 ${
                      seat.status === 'claimed' || seat.status === 'locked'
                        ? 'border-[var(--cyan)] bg-[var(--cyan-wash)] text-[oklch(35% 0.09 205)]'
                        : 'border-[var(--line)] bg-[var(--surface)] text-[var(--muted)]'
                    }`}
                    title={
                      seat.status === 'claimed' || seat.status === 'locked'
                        ? `Seat ${seat.positionNumber} — claimed`
                        : `Seat ${seat.positionNumber} — open`
                    }
                  >
                    <span className="tnum text-sm font-bold">{seat.positionNumber}</span>
                    {shownMember(seat.positionNumber, members) && (
                      <>
                        <span className="absolute left-1/2 bottom-1 -translate-x-1/2 text-[9px] font-semibold uppercase tracking-wide">
                          you
                        </span>
                        <span className="absolute inset-1 rounded-lg ring-1 ring-inset ring-[var(--cyan)]" aria-hidden="true" />
                      </>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-[var(--muted)]">
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm bg-[var(--cyan)]" /> Claimed
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2.5 w-2.5 rounded-sm border border-[var(--line)] bg-[var(--surface)]" /> Open
                </span>
                <span className="ml-auto">
                  {ajo.positionsFilled}/{ajo.positionsTotal} seats
                </span>
              </div>
            </Card>
          </section>
        )}

        {/* Organizer action: open enrollment / invite */}
        {isOrganizer && (ajo.status === 'draft' || ajo.status === 'enrollment') && (
          <section className="mt-8">
            <Card className="p-6">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="max-w-md">
                  <h2 className="text-lg font-semibold tracking-tight">
                    {ajo.status === 'draft' ? 'Open enrollment' : 'Still filling'}
                  </h2>
                  <p className="mt-1 text-sm leading-relaxed text-[var(--muted)]">
                    {ajo.status === 'draft'
                      ? `Enrollment runs exactly five days from the moment you open it. If the last seat is not claimed in that window, the Ajo cancels and every contribution is refunded in full.`
                      : `Every member sees this rail and the countdown. The Ajo activates the instant the last seat claims itself — no button needed.`}
                  </p>
                </div>
                <div className="flex gap-3">
                  {ajo.status === 'draft' && (
                    <Button onClick={() => void openEnrollmentRemote(id, setError, () => void load())}>
                      Open enrollment
                    </Button>
                  )}
                  <Button variant="secondary" onClick={() => setInviteOpen(true)}>
                    <UserPlus className="h-4 w-4" aria-hidden="true" /> Invite members
                  </Button>
                </div>
              </div>
            </Card>
          </section>
        )}

        {/* The roster */}
        <section className="mt-8" aria-label="Roster">
          <h2 className="mb-3 text-lg font-semibold tracking-tight">The roster</h2>
          <Card className="divide-y divide-[var(--line)]">
            {members.length === 0 ? (
              <p className="p-6 text-sm text-[var(--muted)]">No members yet.</p>
            ) : (
              members.map((member, i) => (
                <div key={member.userId} className="flex items-center gap-3 p-4">
                  <span
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                      ajo.yourRole === 'organizer' && i === 0
                        ? 'bg-[var(--gold-wash)] text-[oklch(45% 0.1 84)]'
                        : 'bg-[var(--primary-wash)] text-[var(--primary)]'
                    }`}
                  >
                    {initials(member.fullName)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold">
                      {member.fullName}
                      {member.userId === detail.ajo.organizerUserId && (
                        <span className="ml-2 inline-flex items-center gap-1 text-xs font-medium text-[var(--muted)]">
                          <Crown className="h-3.5 w-3.5 text-[var(--gold)]" aria-hidden="true" />
                          organizer
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-[var(--muted)]">
                      {member.positionNumber !== null ? `Seat ${member.positionNumber}` : 'No seat yet'}
                    </p>
                  </div>
                  <span className="tnum text-sm font-semibold text-[var(--ink)]">
                    {member.joinedAt ? new Date(member.joinedAt).toLocaleDateString('en-NG', { day: 'numeric', month: 'short' }) : '—'}
                  </span>
                </div>
              ))
            )}
          </Card>
        </section>

        {/* The bottom summary line */}
        <p className="mt-8 text-center text-xs text-[var(--muted)]">
          {naira(ajo.contributionKobo)} · {frequencyLabel(ajo.frequency)} on {dayLabel(ajo.collectionDay)} · {ajo.totalRounds} rounds · organized by {isOrganizer ? 'you' : 'the organizer'}
        </p>

        {inviteOpen && (
          <InviteModal
            ajoId={id}
            onClose={() => setInviteOpen(false)}
            onInvited={(invitation) => {
              setInviteOpen(false);
              window.setTimeout(() => window.alert(`Invite link created for ${invitation.email}.\n\nOpen it in another browser to join as that member.`), 50);
              void load();
            }}
          />
        )}
      </main>
    </div>
  );

}

async function openEnrollmentRemote(
  id: string,
  setError: (message: string | null) => void,
  reload: () => void,
) {
  setError(null);
  try {
    await api.openEnrollment(id);
    reload();
  } catch (err) {
    setError(err instanceof ApiError ? err.message : 'Could not open enrollment.');
  }
}

function shownMember(positionNumber: number, members: AjoDetailData['members']): boolean {
  return members.some((member) => member.positionNumber === positionNumber);
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('') || '?';
}
function InviteModal({
  ajoId,
  onClose,
  onInvited,
}: {
  ajoId: string;
  onClose: () => void;
  onInvited: (invitation: { email: string; token: string }) => void;
}) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{ email: string; token: string } | null>(null);
  const linkRef = useRef<HTMLInputElement | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError('Enter a valid email address.');
      return;
    }
    setBusy(true);
    try {
      const response = await api.createInvite(ajoId, [{ name: name.trim() || undefined, email: email.trim() }]);
      const invitation = response.invitations[0];
      if (invitation === undefined) {
        throw new ApiError(500, 'No invitation came back.');
      }
      setResult({ email: invitation.email, token: invitation.token });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create the invitation.');
    } finally {
      setBusy(false);
    }
  }

  const link = result === null ? '' : `${window.location.origin}/join/${result.token}`;

  function copy() {
    if (result === null) {
      return;
    }
    void navigator.clipboard?.writeText(link).then(
      () => onInvited(result),
      () => window.alert(`Invite link:\n${link}`),
    );
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-[var(--deep)]/60 backdrop-blur-sm sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label="Invite a member"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-t-2xl bg-[var(--surface)] p-6 shadow-xl sm:rounded-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">
              {result === null ? 'Invite a member' : 'Your invite link'}
            </h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {result === null
                ? 'The invitee takes the seat in the order they join. Share the link — or have them register with this email and accept from the dashboard.'
                : 'Share the link below. They see the rules before they accept.'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-[var(--muted)] transition-colors hover:bg-[var(--cloud)] hover:text-[var(--ink)]"
            aria-label="Close"
          >
            <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        {result === null ? (
          <form onSubmit={submit} className="mt-6 space-y-4">
            <Field label="Their name" hint="Optional — used on the invite and the roster.">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Chinedu Okeke"
                autoFocus
              />
            </Field>
            <Field label="Their email" hint="They need this exact address to accept — the invitation is bound to it.">
              <Input
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                type="email"
                placeholder="they@example.com"
                required
              />
            </Field>
            <ErrorBanner message={error} />
            <Button type="submit" loading={busy} className="w-full">
              Create invite link
            </Button>
          </form>
        ) : (
          <div className="mt-6">
            <div className="flex items-center gap-2 rounded-lg border border-[var(--line)] bg-[var(--cloud)] px-3 py-2.5">
              <Link2 className="h-4 w-4 shrink-0 text-[var(--primary)]" aria-hidden="true" />
              <input
                ref={linkRef}
                readOnly
                value={link}
                onFocus={(event) => event.currentTarget.select()}
                className="w-full min-w-0 bg-transparent text-sm text-[var(--ink)] outline-none"
                aria-label="Invite link"
              />
            </div>
            <div className="mt-4 flex gap-3">
              <Button onClick={copy} className="flex-1">
                <Copy className="h-4 w-4" aria-hidden="true" /> Copy link
              </Button>
              <Button variant="secondary" onClick={() => { setResult(null); setEmail(''); }}>
                Another invite
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
