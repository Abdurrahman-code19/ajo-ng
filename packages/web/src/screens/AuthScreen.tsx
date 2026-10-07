import { useState, type FormEvent, type ReactNode } from 'react';
import { ShieldCheck, WalletCards, UsersRound } from 'lucide-react';
import { api, ApiError } from '../api';
import { useAuth } from '../auth';
import { Button, ErrorBanner, Field, Input } from '../components/ui';

type Mode = 'login' | 'register';

const PASSWORD_HINT =
  'At least 10 characters. Long and ordinary beats short and random.';

export function AuthScreen() {
  const { login } = useAuth();
  const [mode, setMode] = useState<Mode>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [needsVerification, setNeedsVerification] = useState<string | null>(null);
  const [mailArrived, setMailArrived] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (mode === 'login') {
      setBusy(true);
      try {
        await login(email.trim(), password);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Could not sign in.');
      } finally {
        setBusy(false);
      }
      return;
    }

    // register
    setBusy(true);
    try {
      await api.register({
        email: email.trim(),
        password,
        fullName: fullName.trim(),
        phone: freshPhone(phone.trim()),
        acceptedTerms: true,
        acceptedPrivacy: true,
      });
      setNeedsVerification(email.trim());
      void pollMailbox(email.trim());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not create your account.');
    } finally {
      setBusy(false);
    }
  }

  /** Poll the dev "mailbox" (scripts/dev-mailbox.mjs) for the email. */
  async function pollMailbox(mail: string) {
    const deadline = Date.now() + 15000;
    while (Date.now() < deadline) {
      try {
        const inbox = await fetch(`/mailbox/inbox?email=${encodeURIComponent(mail)}`).then((r) =>
          r.json(),
        );
        if (inbox && inbox.message && inbox.token) {
          setVerificationCode(inbox.token);
          setMailArrived(true);
          return;
        }
      } catch {
        // mailbox not running; let the user type the code from the API log
      }
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }
  }

  async function verify() {
    setError(null);
    setBusy(true);
    try {
      const state = await api.verifyEmail(verificationCode.trim());
      await loginCheck(state.verified ? needsVerification ?? email : null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not verify that code.');
    } finally {
      setBusy(false);
    }
  }

  async function loginCheck(mail: string | null) {
    if (mail === null) {
      return;
    }
    try {
      await login(mail, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Account verified — now sign in.');
      setNeedsVerification(null);
      setMode('login');
      setPassword(password);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_440px]">
      {/* The signed-out voice: mission + trust, on deep navy */}
      <div className="relative hidden overflow-hidden bg-[var(--deep)] text-white lg:block">
        <img
          src="/ajo-secondary.png"
          alt=""
          className="absolute left-8 top-8 h-10 w-auto"
          aria-hidden="true"
        />
        <div className="relative z-10 flex h-full flex-col justify-end p-12">
          <h1 className="max-w-xl text-4xl font-semibold leading-tight tracking-tight">
            Your Ajo. Your Story.
          </h1>
          <p className="mt-4 max-w-md text-lg leading-relaxed text-white/70">
            Bring the people you trust into a rotating savings group of 5 to 20.
            Contributions are recorded, payouts are scheduled, and everybody
            takes their turn.
          </p>
          <ul className="mt-10 flex flex-wrap gap-6">
            <TrustItem icon={<ShieldCheck className="h-5 w-5" />} label="Protected by law" />
            <TrustItem icon={<WalletCards className="h-5 w-5" />} label="2% platform fee" />
            <TrustItem icon={<UsersRound className="h-5 w-5" />} label="5–20 members" />
          </ul>
        </div>
        <div className="pointer-events-none absolute inset-0 opacity-40">
          <div
            className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-[var(--primary)] blur-[110px]"
            aria-hidden="true"
          />
          <div
            className="absolute -bottom-32 -left-16 h-80 w-80 rounded-full bg-[var(--cyan)]/60 blur-[110px]"
            aria-hidden="true"
          />
        </div>
      </div>

      {/* The form */}
      <div className="flex items-center justify-center px-4 py-12 sm:px-8">
        <div className="w-full max-w-sm">
          <img src="/ajo-mark.png" alt="AJO.ng" className="mb-8 h-10 w-auto lg:hidden" />

          {needsVerification !== null ? (
            <>
              <h2 className="text-2xl font-semibold tracking-tight">Check your inbox</h2>
              <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
                We emailed a verification code to <strong className="text-[var(--ink)]">{needsVerification}</strong>.
                Enter it below to confirm your account.
              </p>
              <div
                className={`mt-4 flex items-center gap-2 rounded-lg px-3.5 py-3 text-sm ${
                  mailArrived
                    ? 'bg-[oklch(96% 0.03 155)] text-[var(--success)]'
                    : 'bg-[var(--cloud)] text-[var(--muted)]'
                }`}
                aria-live="polite"
              >
                <span
                  className={`h-2 w-2 rounded-full ${mailArrived ? 'bg-[var(--success)]' : 'animate-pulse bg-[var(--gold)]'}`}
                  aria-hidden="true"
                />
                {mailArrived
                  ? 'Mailbox synced — your code is filled in.'
                  : verificationCode !== ''
                    ? 'Checking your mailbox…'
                    : 'Waiting for the email to arrive…'}
              </div>
              <form onSubmit={(e) => { e.preventDefault(); void verify(); }} className="mt-6 space-y-4">
                <Field label="Verification code">
                  <Input
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    placeholder="e.g. 4f2a91c3"
                    autoFocus
                    required
                  />
                </Field>
                <Button type="submit" loading={busy} className="w-full">
                  Verify and continue
                </Button>
              </form>
            </>
          ) : (
            <>
              <h2 className="text-2xl font-semibold tracking-tight">
                {mode === 'login' ? 'Welcome back' : 'Start your Ajo'}
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
                {mode === 'login'
                  ? 'Sign in to see your Ajos and what is due next.'
                  : 'Create an account to begin a group, or join one you were invited to.'}
              </p>

              <form onSubmit={submit} className="mt-6 space-y-4">
                {mode === 'register' && (
                  <>
                    <Field label="Full name">
                      <Input
                        value={fullName}
                        onChange={(e) => setFullName(e.target.value)}
                        placeholder="Ada Obi"
                        autoComplete="name"
                        required
                      />
                    </Field>
                    <Field label="Phone">
                      <Input
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="0803 123 4567"
                        type="tel"
                        autoComplete="tel"
                      />
                    </Field>
                  </>
                )}
                <Field label="Email">
                  <Input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    type="email"
                    placeholder="you@example.com"
                    autoComplete="email"
                    required
                  />
                </Field>
                <Field
                  label="Password"
                  hint={mode === 'register' ? PASSWORD_HINT : undefined}
                >
                  <Input
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    type="password"
                    placeholder="••••••••••"
                    autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                    required
                    minLength={mode === 'register' ? 10 : undefined}
                  />
                </Field>

                <ErrorBanner message={error} />

                <Button type="submit" loading={busy} className="w-full">
                  {mode === 'login' ? 'Sign in' : 'Create account'}
                </Button>
              </form>

              <p className="mt-6 text-center text-sm text-[var(--muted)]">
                {mode === 'login' ? (
                  <>
                    New to AJO.ng?{' '}
                    <button
                      type="button"
                      className="font-semibold text-[var(--primary)] hover:underline"
                      onClick={() => { setMode('register'); setError(null); }}
                    >
                      Create an account
                    </button>
                  </>
                ) : (
                  <>
                    Already a member?{' '}
                    <button
                      type="button"
                      className="font-semibold text-[var(--primary)] hover:underline"
                      onClick={() => { setMode('login'); setError(null); }}
                    >
                      Sign in
                    </button>
                  </>
                )}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function TrustItem({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <li className="flex items-center gap-2.5 text-sm font-medium text-white/85">
      <span className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-[var(--cyan)]">
        {icon}
      </span>
      {label}
    </li>
  );
}

function freshPhone(phone: string): string {
  const digits = phone.replace(/[^\d+]/g, '');
  if (digits === '') {
    return '+2348000000000';
  }
  return digits;
}