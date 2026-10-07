import { useState, type FormEvent } from 'react';
import { ArrowLeft, Info } from 'lucide-react';
import { api, ApiError } from '../api';
import type { AjoFrequency, CollectionDay } from '../api-types';
import { useAuth } from '../auth';
import { TopBar } from '../components/TopBar';
import { Button, Card, ErrorBanner, Field, Input } from '../components/ui';

const FREQUENCIES: { value: AjoFrequency; label: string; hint: string }[] = [
  { value: 'WEEKLY', label: 'Weekly', hint: 'every 7 days' },
  { value: 'BIWEEKLY', label: 'Every 2 weeks', hint: 'every 14 days' },
  { value: 'MONTHLY', label: 'Monthly', hint: 'same day each month' },
];

const DAYS: { value: CollectionDay; label: string }[] = [
  { value: 'MONDAY', label: 'Monday' },
  { value: 'TUESDAY', label: 'Tuesday' },
  { value: 'WEDNESDAY', label: 'Wednesday' },
  { value: 'THURSDAY', label: 'Thursday' },
  { value: 'FRIDAY', label: 'Friday' },
  { value: 'SATURDAY', label: 'Saturday' },
  { value: 'SUNDAY', label: 'Sunday' },
];

const RUELS = [
  'Your Ajo has exactly one seat per member — you and every invitee rounds to the same size.',
  'Membership has no payout order change after seats are locked, so agree on the order up front.',
  'A default is private between the member, you, and Ajo.ng risk. No public shaming, never.',
];

export function CreateAjo() {
  const { navigate } = useAuth();
  const [name, setName] = useState('');
  const [contribution, setContribution] = useState('1000');
  const [frequency, setFrequency] = useState<AjoFrequency>('WEEKLY');
  const [collectionDay, setCollectionDay] = useState<CollectionDay>('FRIDAY');
  const [members, setMembers] = useState('10');
  const [error, setError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const contributionKobo = Math.max(0, Math.round(Number(contribution) * 100));
  const memberCount = Math.max(5, Math.min(20, Math.round(Number(members) || 10)));
  // Rounds equal members (CANONICAL §3): a ten-member Ajo runs ten rounds.
  const rounds = memberCount;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setFieldError(null);

    if (Number(contribution) < 1000) {
      setFieldError('A contribution must be at least ₦1,000.');
      return;
    }
    if (!name.trim() || name.trim().length < 3) {
      setFieldError('Give your Ajo a name — at least three characters.');
      return;
    }

    setBusy(true);
    try {
      const result = await api.createAjo({
        name: name.trim(),
        contributionKobo,
        currency: 'NGN',
        frequency,
        collectionDay,
        durationRounds: rounds,
        maxMembers: memberCount,
        startDate: nextDay(collectionDay),
      });
      navigate({ kind: 'ajo', id: result.ajo.id });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create the Ajo.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-[var(--cloud)]">
      <TopBar onHome={() => navigate({ kind: 'dashboard' })} />
      <main className="mx-auto max-w-2xl px-4 py-8 sm:px-6">
        <button
          type="button"
          onClick={() => navigate({ kind: 'dashboard' })}
          className="inline-flex items-center gap-1.5 text-sm font-semibold text-[var(--muted)] transition-colors hover:text-[var(--primary)]"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to My Ajos
        </button>

        <h1 className="mt-4 text-3xl font-semibold tracking-tight">Create an Ajo</h1>
        <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
          Set the rules once, before anybody is invited. You can change nothing
          about an Ajo once enrollment opens, so read each field as a promise.
        </p>

        <form onSubmit={submit} className="mt-8 space-y-6">
          <Card className="p-6">
            <Field label="Ajo name">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Market Sisters"
                required
                minLength={3}
                maxLength={80}
              />
            </Field>
          </Card>

          <Card className="p-6">
            <h2 className="text-base font-semibold">The saving</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">How much each member pays, and how often.</p>
            <div className="mt-4 space-y-4">
              <Field
                label="Contribution per member"
                hint="The base obligation. A 2% platform fee applies on top — it is your charge, not the pool's."
              >
                <div className="relative">
                  <span className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-base font-semibold text-[var(--muted)]">
                    ₦
                  </span>
                  <Input
                    className="pl-8"
                    value={contribution}
                    onChange={(e) => setContribution(e.target.value.replace(/[^\d]/g, ''))}
                    inputMode="numeric"
                    required
                  />
                </div>
              </Field>

              <fieldset>
                <legend className="mb-1.5 block text-sm font-semibold">How often</legend>
                <div className="grid gap-2 sm:grid-cols-3">
                  {FREQUENCIES.map((option) => (
                    <label
                      key={option.value}
                      className={`cursor-pointer rounded-lg border px-3 py-2.5 transition-colors ${
                        frequency === option.value
                          ? 'border-[var(--primary)] bg-[var(--primary-wash)]'
                          : 'border-[var(--line)] bg-[var(--surface)] hover:border-[var(--primary)]/60'
                      }`}
                    >
                      <input
                        type="radio"
                        name="frequency"
                        value={option.value}
                        checked={frequency === option.value}
                        onChange={() => setFrequency(option.value)}
                        className="sr-only"
                      />
                      <span className="block text-sm font-semibold">{option.label}</span>
                      <span className="block text-xs text-[var(--muted)]">{option.hint}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              <fieldset>
                <legend className="mb-1.5 block text-sm font-semibold">Collect on</legend>
                <div className="flex flex-wrap gap-1.5">
                  {DAYS.map((day) => (
                    <label
                      key={day.value}
                      className={`cursor-pointer rounded-full border px-3 py-1.5 text-sm font-medium transition-colors ${
                        collectionDay === day.value
                          ? 'border-[var(--primary)] bg-[var(--primary-wash)] text-[var(--primary)]'
                          : 'border-[var(--line)] bg-[var(--surface)] text-[var(--muted)] hover:border-[var(--primary)]/60'
                      }`}
                    >
                      <input
                        type="radio"
                        name="collectionDay"
                        value={day.value}
                        checked={collectionDay === day.value}
                        onChange={() => setCollectionDay(day.value)}
                        className="sr-only"
                      />
                      {day.label}
                    </label>
                  ))}
                </div>
              </fieldset>
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-base font-semibold">The group</h2>
            <Field
              label="Number of members"
              hint="Between 5 and 20. You count as one — a ten-member Ajo is you plus nine invitees."
            >
              <div className="flex items-center gap-4">
                <Input
                  className="max-w-[7rem]"
                  value={members}
                  onChange={(e) => setMembers(e.target.value.replace(/[^\d]/g, ''))}
                  inputMode="numeric"
                  required
                />
                <div className="text-sm text-[var(--muted)]">
                  {memberCount} members · <span className="tnum font-semibold text-[var(--ink)]">{rounds} rounds</span> of
                  saving
                </div>
              </div>
            </Field>
          </Card>

          <ol className="space-y-2 rounded-xl border border-dashed border-[var(--line)] bg-[var(--surface)] p-5 text-sm text-[var(--muted)]">
            {RUELS.map((rule, i) => (
              <li key={i} className="flex gap-2.5">
                <Info className="mt-0.5 h-4 w-4 shrink-0 text-[var(--cyan)]" aria-hidden="true" />
                <span>{rule}</span>
              </li>
            ))}
          </ol>

          <ErrorBanner message={error ?? fieldError} />

          <Button type="submit" size="lg" loading={busy} className="w-full">
            Create the Ajo
          </Button>
        </form>
      </main>
    </div>
  );
}

function nextDay(day: CollectionDay): string {
  const index = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'].indexOf(day);
  const today = new Date();
  const diff = (index - today.getDay() + 7) % 7 || 7;
  const next = new Date(today);
  next.setDate(today.getDate() + diff);
  return next.toISOString().slice(0, 10);
}