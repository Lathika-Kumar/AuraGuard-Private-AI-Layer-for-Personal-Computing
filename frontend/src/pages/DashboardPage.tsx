import { useEffect, useState } from 'react';
import { fetchHealth, fetchDocuments } from '../services/api';

export default function DashboardPage() {
  const [health, setHealth] = useState<{ status?: string; python_version?: string } | null>(null);
  const [docs, setDocs] = useState<Array<{ id: number }>>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [healthResponse, documentsResponse] = await Promise.all([fetchHealth(), fetchDocuments()]);
        setHealth(healthResponse);
        setDocs(documentsResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data.');
      }
    }
    void load();
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Dashboard</p>
          <h2 className="mt-2 text-3xl font-bold">System overview</h2>
        </div>
      </header>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Documents indexed" value={docs.length} />
        <StatCard label="Memories stored" value={0} />
        <StatCard label="Privacy events" value={0} />
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="text-lg font-semibold">Device status</h3>
        <div className="mt-4 space-y-2 text-sm text-slate-300">
          <p>Status: {health?.status ?? 'Loading...'}</p>
          <p>Python: {health?.python_version ?? 'Loading...'}</p>
          <p>Local-first mode: enabled</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-cyan-300">{value}</p>
    </div>
  );
}
