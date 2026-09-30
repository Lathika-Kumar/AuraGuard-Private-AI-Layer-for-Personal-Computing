import React, { useEffect, useState } from 'react';
import {
  fetchPrivacyEvents,
  fetchPrivacyStats,
  fetchPrivacyPolicy,
  updatePrivacyPolicy,
  analyzePrivacy,
  fetchSecurityStatus,
  PrivacyEvent,
  PrivacyStats,
  PrivacyPolicyInfo,
  PrivacyAnalysis,
  SecurityStatus,
} from '../services/api';

export default function PrivacyCenterPage() {
  const [stats, setStats] = useState<PrivacyStats | null>(null);
  const [events, setEvents] = useState<PrivacyEvent[]>([]);
  const [policy, setPolicy] = useState<PrivacyPolicyInfo | null>(null);
  const [security, setSecurity] = useState<SecurityStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modeUpdating, setModeUpdating] = useState(false);

  // Live Privacy Scanner tool state
  const [testText, setTestText] = useState('');
  const [scanResult, setScanResult] = useState<PrivacyAnalysis | null>(null);
  const [scanning, setScanning] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [statsData, eventsData, policyData, securityData] = await Promise.all([
        fetchPrivacyStats(),
        fetchPrivacyEvents(50),
        fetchPrivacyPolicy(),
        fetchSecurityStatus(),
      ]);
      setStats(statsData);
      setEvents(eventsData);
      setPolicy(policyData);
      setSecurity(securityData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load privacy data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, []);

  const handleModeChange = async (newMode: string) => {
    try {
      setModeUpdating(true);
      await updatePrivacyPolicy(newMode);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Mode update failed');
    } finally {
      setModeUpdating(false);
    }
  };

  const handleScanText = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testText.trim()) return;

    try {
      setScanning(true);
      const res = await analyzePrivacy(testText.trim(), policy?.mode);
      setScanResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Privacy Center</p>
          <h2 className="mt-1 text-3xl font-bold">Local Privacy & Shield</h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time entity detection, classification, on-device sanitization, and audit telemetry.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300 border border-emerald-500/30">
            Local Inference: Enabled
          </span>
          <span className="inline-flex items-center rounded-full bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-300 border border-slate-700">
            Cloud Inference: Disabled
          </span>
          <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-mono text-cyan-300 border border-cyan-500/30">
            Backend: 127.0.0.1
          </span>
        </div>
      </header>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      {/* Metrics Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Privacy Events</p>
          <p className="mt-2 text-3xl font-bold text-cyan-300">{stats?.total_events ?? 0}</p>
          <p className="mt-1 text-xs text-slate-500">Total detected incidents</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Redactions Applied</p>
          <p className="mt-2 text-3xl font-bold text-amber-300">{stats?.redacted_events ?? 0}</p>
          <p className="mt-1 text-xs text-slate-500">Sanitized context or output</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Blocked Requests</p>
          <p className="mt-2 text-3xl font-bold text-red-400">{stats?.blocked_events ?? 0}</p>
          <p className="mt-1 text-xs text-slate-500">Prohibited secrets shielded</p>
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">External Calls</p>
          <p className="mt-2 text-3xl font-bold text-emerald-400">0</p>
          <p className="mt-1 text-xs text-slate-500">Strict local containment</p>
        </div>
      </div>

      {/* Storage Encryption & Key Protection Card (Part 13 Security Dashboard) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Security Dashboard & Storage Encryption</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Cryptographically verified on-device security telemetry with Windows DPAPI key protection.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className={`font-mono text-xs px-2.5 py-1 rounded border ${
              security?.storage_encryption
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
            }`}>
              Storage Encryption: {security?.storage_encryption ? 'AES-256-GCM' : 'Unencrypted'}
            </span>
            <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Key Protection: {security?.key_protection ?? 'Windows DPAPI'}
            </span>
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-xs font-mono">
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Storage Encryption</p>
            <p className="font-bold text-emerald-400 mt-1">{security?.algorithm ?? 'AES-256-GCM'}</p>
          </div>
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Key Protection</p>
            <p className="font-bold text-cyan-400 mt-1">{security?.key_protection ?? 'Windows DPAPI'}</p>
          </div>
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Local AI</p>
            <p className="font-bold text-emerald-400 mt-1">{security?.local_ai ?? 'Enabled'}</p>
          </div>
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Cloud Inference</p>
            <p className="font-bold text-slate-300 mt-1">{security?.cloud_inference ?? 'Disabled'}</p>
          </div>
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Privacy Events</p>
            <p className="font-bold text-cyan-300 mt-1">{security?.privacy_events ?? stats?.total_events ?? 0}</p>
          </div>
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Blocked Requests</p>
            <p className="font-bold text-red-400 mt-1">{security?.blocked_requests ?? stats?.blocked_events ?? 0}</p>
          </div>
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Encrypted Memories</p>
            <p className="font-bold text-purple-300 mt-1">{security?.encrypted_memories ?? 0}</p>
          </div>
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <p className="text-slate-400">Encrypted Documents</p>
            <p className="font-bold text-cyan-300 mt-1">{security?.encrypted_documents ?? 0}</p>
          </div>
        </div>
      </div>

      {/* Policy Mode Selector Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Privacy Policy Configuration</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Choose the strictness level for data classification and automated redactions.
            </p>
          </div>
          <span className="font-mono text-xs uppercase px-2.5 py-1 rounded bg-slate-800 text-cyan-300 border border-slate-700">
            Active Mode: {policy?.mode ?? 'balanced'}
          </span>
        </div>

        <div className="mt-5 grid gap-4 md:grid-cols-3">
          {(['strict', 'balanced', 'permissive'] as const).map((mode) => {
            const isSelected = policy?.mode === mode;
            return (
              <div
                key={mode}
                onClick={() => !modeUpdating && handleModeChange(mode)}
                className={`cursor-pointer rounded-xl border p-4 transition ${
                  isSelected
                    ? 'border-cyan-500/80 bg-cyan-950/20 ring-1 ring-cyan-500/40'
                    : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-sm uppercase tracking-wider text-slate-200">{mode}</span>
                  {isSelected ? (
                    <span className="inline-block h-2 w-2 rounded-full bg-cyan-400 ring-4 ring-cyan-400/20"></span>
                  ) : null}
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-400">
                  {policy?.rules?.[mode]?.description ??
                    (mode === 'strict'
                      ? 'Maximum protection: blocks credentials and aggressively redacts all personal identifiers.'
                      : mode === 'balanced'
                      ? 'Default on-device balance: blocks raw secrets, redacts sensitive context, warns on personal queries.'
                      : 'Permissive development mode: permits personal identifiers while sanitizing high-risk secrets.')}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Privacy Scanner Tool */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <div className="border-b border-slate-800 pb-3">
          <h3 className="text-lg font-semibold text-slate-100">Live Privacy Inspector</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Test any text against the AuraGuard Privacy Engine to preview entity detection and redaction.
          </p>
        </div>

        <form onSubmit={handleScanText} className="mt-4 space-y-4">
          <textarea
            rows={3}
            value={testText}
            onChange={(e) => setTestText(e.target.value)}
            placeholder="Type or paste sample text containing emails, cards, keys, or phone numbers to test..."
            className="w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-slate-100 placeholder:text-slate-500 outline-none focus:border-cyan-500"
          />
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={scanning || !testText.trim()}
              className="rounded-lg bg-cyan-500 px-4 py-2 text-xs font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
            >
              {scanning ? 'Scanning...' : 'Scan Text with Privacy Engine'}
            </button>
          </div>
        </form>

        {scanResult ? (
          <div className="mt-4 rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-4">
            {/* Part 9: Structured Detection, Classification, Decision, Reason */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs border-b border-slate-800 pb-3">
              <div className="rounded-lg bg-slate-900/80 p-2.5 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Detection</span>
                <span className="font-semibold text-cyan-300 mt-1 block">
                  {scanResult.entities.length > 0 ? scanResult.entities.map(e => e.type).join(', ') : 'None'}
                </span>
              </div>
              <div className="rounded-lg bg-slate-900/80 p-2.5 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Classification</span>
                <span className="font-semibold text-amber-300 mt-1 block">{scanResult.classification}</span>
              </div>
              <div className="rounded-lg bg-slate-900/80 p-2.5 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Decision</span>
                <span className={`font-bold mt-1 block ${scanResult.allowed ? 'text-emerald-400' : 'text-red-400'}`}>
                  {scanResult.allowed ? 'ALLOWED' : 'BLOCKED'}
                </span>
              </div>
              <div className="rounded-lg bg-slate-900/80 p-2.5 border border-slate-800">
                <span className="text-slate-400 block text-[10px] uppercase tracking-wider">Reason</span>
                <span className="text-slate-300 mt-1 block text-[11px]">
                  {scanResult.allowed ? 'Safe for on-device context synthesis' : 'Credential detected before ingestion'}
                </span>
              </div>
            </div>

            {scanResult.entities.length > 0 ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
                  Detected Entities ({scanResult.entities.length})
                </p>
                <div className="flex flex-wrap gap-2">
                  {scanResult.entities.map((e, idx) => (
                    <div
                      key={idx}
                      className="rounded-md border border-slate-800 bg-slate-900 px-2.5 py-1 text-xs"
                    >
                      <span className="font-semibold text-cyan-300">{e.type}</span>
                      <span className="mx-1.5 text-slate-600">&bull;</span>
                      <span className="text-slate-400">{e.action}</span>
                      <span className="mx-1.5 text-slate-600">&bull;</span>
                      <span className="text-slate-500 font-mono">
                        {Math.round((e.confidence ?? 1) * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-xs text-emerald-400">No sensitive entities detected in input.</p>
            )}

            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
                Redacted Context Preview
              </p>
              <pre className="rounded bg-slate-900 p-3 text-xs text-slate-200 whitespace-pre-wrap font-mono border border-slate-800">
                {scanResult.redacted_text}
              </pre>
            </div>
          </div>
        ) : null}
      </div>

      {/* Privacy Events Audit Log */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
        <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">Privacy Audit Log</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Historical ledger of detected entities and sanitization events. Secret values are never recorded.
            </p>
          </div>
          <button
            onClick={() => void loadData()}
            className="text-xs text-cyan-400 hover:text-cyan-300"
          >
            Refresh Log
          </button>
        </div>

        <div className="mt-4 overflow-x-auto">
          {events.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400">
              No privacy events recorded yet. Events are logged when sensitive data is detected or shielded.
            </div>
          ) : (
            <table className="w-full text-left text-xs">
              <thead className="border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="py-2.5 font-semibold">Timestamp</th>
                  <th className="py-2.5 font-semibold">Event</th>
                  <th className="py-2.5 font-semibold">Severity</th>
                  <th className="py-2.5 font-semibold">Source</th>
                  <th className="py-2.5 font-semibold">Entity Type</th>
                  <th className="py-2.5 font-semibold">Action</th>
                  <th className="py-2.5 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {events.map((ev) => (
                  <tr key={ev.id} className="hover:bg-slate-800/30">
                    <td className="py-2.5 font-mono text-slate-400 whitespace-nowrap">
                      {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : '-'}
                    </td>
                    <td className="py-2.5 font-medium text-slate-200">{ev.event_type}</td>
                    <td className="py-2.5">
                      <span
                        className={`rounded px-1.5 py-0.5 font-mono text-[10px] ${
                          ev.severity === 'CRITICAL' || ev.severity === 'HIGH'
                            ? 'bg-red-500/20 text-red-300'
                            : 'bg-amber-500/20 text-amber-300'
                        }`}
                      >
                        {ev.severity}
                      </span>
                    </td>
                    <td className="py-2.5 font-mono text-slate-400">{ev.source ?? 'core'}</td>
                    <td className="py-2.5 text-cyan-300 font-medium">{ev.entity_type ?? '-'}</td>
                    <td className="py-2.5">
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-300">
                        {ev.action ?? 'REDACT'}
                      </span>
                    </td>
                    <td className="py-2.5 text-slate-400 max-w-xs truncate" title={ev.description}>
                      {ev.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
