import { useEffect } from 'react';
import { AuthProvider, useAuth } from './auth';
import { Dashboard } from './screens/Dashboard';
import { CreateAjo } from './screens/CreateAjo';
import { AjoDetail } from './screens/AjoDetail';
import { AuthScreen } from './screens/AuthScreen';
import { JoinScreen } from './screens/JoinScreen';

function Router() {
  const { view } = useAuth();
  switch (view.kind) {
    case 'auth':
      return <AuthScreen />;
    case 'dashboard':
      return <Dashboard />;
    case 'create':
      return <CreateAjo />;
    case 'ajo':
      return <AjoDetail key={view.id} id={view.id} />;
    case 'join':
      return <JoinScreen key={view.token} token={view.token} />;
  }
}

function Shell() {
  const { refresh, booting } = useAuth();
  useEffect(() => {
    void refresh();
  }, [refresh]);

  if (booting) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--cloud)]">
        <div className="flex flex-col items-center gap-3">
          <span className="h-8 w-8 animate-spin rounded-full border-[3px] border-[var(--line)] border-t-[var(--primary)]" />
          <p className="text-sm text-[var(--muted)]">Loading your Ajos…</p>
        </div>
      </div>
    );
  }
  return <Router />;
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}