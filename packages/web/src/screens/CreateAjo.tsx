import { useState, type FormEvent } from 'react';
import { ArrowLeft, ArrowRight, Info } from 'lucide-react';
import { api, ApiError } from '../api';
import type { AjoFrequency, CollectionDay } from '../api-types';
import { useAuth } from '../auth';
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

const RULES = [
  'Your Ajo has exactly one seat per member — you and every invitee rounds to the same size.',
  'Membership has no payout order change after seats are locked, so agree on the order up front.',
  'A default is private between the member, you, and Ajo.ng risk. No public shaming, never.',
];

const STEPS = ['The Ajo', 'The rhythm', 'The group', 'Review'];

export function CreateAjo() {
  const { navigate } = useAuth();
  const [step, setStep] = useState(0);
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

  function next() {
    setFieldError(null);
    if (step === 0) {
      if (Number(contribution) < 1000) {
        setFieldError('A contribution must be at least ₦1,000.');
        return;
      }
      if (!name.trim() || name.trim().length < 3) {
        setFieldError('Give your Ajo a name — at least three characters.');
        return;
      }
    }
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function back() {
    setFieldError(null);
    setStep((s) => Math.max(s - 1, 0));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
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

  const isReview = step === STEPS.length - 1;

  return (
    <form onSubmit={submit}>
      {/* Stepper header */}
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">
          Step {step + 1} of {STEPS.length}
          <span className="ml-2 text-[var(--primary)]">{STEPS[step]}</span>
        </p>
        <div className="flex gap-1.5" aria-hidden="true">
          {STEPS.map((label, i) => (
            <span
              key={label}
              className={`h-1.5 rounded-full transition-colors duration-300 ${
                i <= step ? 'bg-gradient-cta' : 'bg-[var(--line)]'
              }`}
              style={{ width: i === step ? '2.25rem' : '1rem' }}
            />
          ))}
        </div>
      </div>

      <Card className="anim-fade-up mt-5 p-6 sm:p-8" key={step}>
        {step === 0 && (
          <div className="space-y-5">
            <div>
              <p className="font-display text-xl font-semibold tracking-tight">Name your Ajo</p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                It travels on every invite and every schedule — make it easy to recognise.
              </p>
            </div>
            <Field label="Ajo name">
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Market Sisters"
                required
                minLength={3}
                maxLength={80}
                autoFocus
              />
            </Field>
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
          </div>
        )}

        {step === 1 && (
          <div className="space-y-6">
            <div>
              <p className="font-display text-xl font-semibold tracking-tight">Set the rhythm</p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                How often the pool collects, and on which day it hits everyone's wallet.
              </p>
            </div>
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
        )}

        {step === 2 && (
          <div className="space-y-5">
            <div>
              <p className="font-display text-xl font-semibold tracking-tight">Build the group</p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Five to twenty. You count as one — a ten-member Ajo is you plus nine invitees.
              </p>
            </div>
            <Field label="Number of members">
              <div className="flex items-center gap-4">
                <Input
                  className="max-w-[7rem]"
                  value={members}
                  onChange={(e) => setMembers(e.target.value.replace(/[^\d]/g, ''))}
                  inputMode="numeric"
                  required
                />
                <div className="text-sm text-[var(--muted)]">
                  {memberCount} members ·{' '}
                  <span className="tnum font-semibold text-[var(--ink)]">{rounds} rounds</span> of
                  saving
                </div>
              </div>
            </Field>
            <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-[var(--muted)]">
              <span
                className="inline-flex items-center gap-1.5 rounded-full bg-[var(--primary-wash)] px-3 py-1.5 font-semibold text-[var(--primary)]"
              >
                ₦{(contributionKobo / 100).toLocaleString('en-NG', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} × {memberCount} members
              </span>
              <span
                className="inline-flex items-center gap-1.5 rounded-full bg-[var(--cyan-wash)] px-3 py-1.5 font-semibold text-[var(--cyan)]"
              >
                Pool per round ₦{((contributionKobo * memberCount) / 100).toLocaleString('en-NG')}
              </span>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-5">
            <div>
              <p className="font-display text-xl font-semibold tracking-tight">Review the promise</p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Nothing changes once enrollment opens — read this as the contract it is.
              </p>
            </div>

            <dl className="divide-y divide-[var(--line)] rounded-xl border border-[var(--line)]">
              {(
                [
                  ['Name', name.trim()],
                  ['Contribution', `₦${(contributionKobo / 100).toLocaleString('en-NG')} / ${FREQUENCIES.find((f) => f.value === frequency)?.label}`],
                  ['Collects on', DAYS.find((d) => d.value === collectionDay)?.label],
                  ['Group size', `${memberCount} members · ${rounds} rounds`],
                  ['Pool per round', `₦${((contributionKobo * memberCount) / 100).toLocaleString('en-NG')}`],
                  ['First collection', dayLabel2(collectionDay)],
                ] as const
              ).map(([label, value]) => (
                <div key={label} className="flex items-center justify-between gap-4 px-4 py-3 sm:px-5">
                  <dt className="text-sm font-medium text-[var(--muted)]">{label}</dt>
                  <dd className="tnum text-right text-sm font-semibold text-[var(--ink)]">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>

            <ol className="space-y-2 rounded-xl border border-dashed border-[var(--line)] bg-[var(--cloud)] p-5 text-sm text-[var(--muted)]">
              {RULES.map((rule, i) => (
                <li key={i} className="flex gap-2.5">
                  <Info className="mt-0.5 h-4 w-4 shrink-0 text-[var(--cyan)]" aria-hidden="true" />
                  <span>{rule}</span>
                </li>
              ))}
            </ol>
          </div>
        )}
      </Card>

      {(error || fieldError) && <ErrorBanner message={error ?? fieldError} />}

      {/* Actions */}
      <div className="mt-6 flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={back}
          className={`inline-flex h-11 items-center gap-1.5 rounded-xl px-4 text-sm font-semibold text-[var(--muted)] transition-colors hover:text-[var(--ink)] ${
            step === 0 ? 'invisible' : ''
          }`}
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back
        </button>
        {isReview ? (
          <Button type="submit" size="lg" loading={busy} className="min-w-[10rem]">
            Create the Ajo
          </Button>
        ) : (
          <Button type="button" onClick={next} size="lg" className="min-w-[10rem]">
            Continue
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Button>
        )}
      </div>
    </form>
  );
}

function dayLabel2(day: CollectionDay): string {
  return DAYS.find((d) => d.value === day)?.label ?? '—';
}

function nextDay(day: CollectionDay): string {
  const index = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'].indexOf(day);
  const today = new Date();
  const diff = (index - today.getDay() + 7) % 7 || 7;
  const next = new Date(today);
  next.setDate(today.getDate() + diff);
  return next.toISOString().slice(0, 10);
}