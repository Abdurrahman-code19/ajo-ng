import { useEffect, useState } from 'react';
import { AuthProvider, useAuth } from './auth';
import { AppShell } from './components/AppShell';
import { Splash } from './components/Splash';
import { Skeleton } from './components/ui';
import { Dashboard } from './screens/Dashboard';
import { CreateAjo } from './screens/CreateAjo';
import { AjoDetail } from './screens/AjoDetail';
import { AuthScreen } from './screens/AuthScreen';
import { JoinScreen } from './screens/JoinScreen';

function RoutedView() {
  const { view } = useAuth();
  switch (view.kind) {
    case 'auth':
      return <AuthScreen />;
    case 'dashboard':
      return (
        <AppShell>
          <Dashboard />
        </AppShell>
      );
    case 'create':
      return (
        <AppShell>
          <CreateAjo />
        </AppShell>
      );
    case 'ajo':
      return (
        <AppShell>
          <AjoDetail key={view.id} id={view.id} />
        </AppShell>
      );
    case 'join':
      return <JoinScreen key={view.token} token={view.token} />;
  }
}

function BootSkeleton() {
  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6">
      <Skeleton className="h-8 w-56" />
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
      <div className="mt-8 space-y-4">
        <Skeleton className="h-44" />
        <Skeleton className="h-44" />
      </div>
    </div>
  );
}

/**
 * Splash → boot → app. The splash is presentational; the app resolves behind
 * the mask (token check, then whatever the view asked for), then fades in.
 */
function Root() {
  const { refresh, booting } = useAuth();
  const [entered, setEntered] = useState(false);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const timer = window.setTimeout(() => setEntered(true), reduced ? 250 : 1850);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-[var(--cloud)] text-[var(--ink)]">
      <Splash leaving={entered} />
      <div className={entered ? 'anim-fade-up' : 'invisible'}>
        {booting ? <BootSkeleton /> : <RoutedView />}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Root />
    </AuthProvider>
  );
}