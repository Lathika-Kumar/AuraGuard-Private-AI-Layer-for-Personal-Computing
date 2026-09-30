import React, { useEffect, useState } from 'react';
import {
  fetchMemories,
  createMemory,
  updateMemory,
  deleteMemory,
  archiveMemory,
  analyzePrivacy,
  cleanupExpiredMemories,
  MemoryItem,
  PrivacyAnalysis,
} from '../services/api';

const MEMORY_TYPES = ['ALL', 'FACT', 'PREFERENCE', 'TASK', 'GOAL', 'NOTE', 'CONTEXT'] as const;

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('active');
  const [searchQuery, setSearchQuery] = useState('');

  // Add / Edit Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState<MemoryItem | null>(null);
  const [formContent, setFormContent] = useState('');
  const [formType, setFormType] = useState('NOTE');
  const [formImportance, setFormImportance] = useState(0.7);
  const [formExpiresAt, setFormExpiresAt] = useState('');
  const [saving, setSaving] = useState(false);
  const [privacyPreview, setPrivacyPreview] = useState<PrivacyAnalysis | null>(null);

  const [userConfirmed, setUserConfirmed] = useState(false);
  const [deletionNotice, setDeletionNotice] = useState<string | null>(null);

  const loadMemories = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchMemories({
        type: selectedType === 'ALL' ? undefined : selectedType,
        status: selectedStatus === 'all' ? undefined : selectedStatus,
        search: searchQuery.trim() || undefined,
        include_expired: true,
      });
      setMemories(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load memories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadMemories();
  }, [selectedType, selectedStatus]);

  // Handle privacy pre-scan when typing in modal
  useEffect(() => {
    if (!formContent.trim()) {
      setPrivacyPreview(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await analyzePrivacy(formContent.trim());
        setPrivacyPreview(res);
      } catch {
        // ignore background error
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [formContent]);

  const openCreateModal = () => {
    setEditingMemory(null);
    setFormContent('');
    setFormType('NOTE');
    setFormImportance(0.7);
    setFormExpiresAt('');
    setPrivacyPreview(null);
    setUserConfirmed(false);
    setIsModalOpen(true);
  };

  const openEditModal = (mem: MemoryItem) => {
    setEditingMemory(mem);
    setFormContent(mem.content);
    setFormType(mem.type);
    setFormImportance(mem.importance);
    setFormExpiresAt(mem.expires_at ? mem.expires_at.slice(0, 16) : '');
    setPrivacyPreview(null);
    setUserConfirmed(true);
    setIsModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formContent.trim() || !userConfirmed) return;

    try {
      setSaving(true);
      setError(null);
      const isoExpiry = formExpiresAt ? new Date(formExpiresAt).toISOString() : null;

      if (editingMemory) {
        await updateMemory(editingMemory.id, {
          content: formContent.trim(),
          type: formType,
          importance: formImportance,
          expires_at: isoExpiry,
        });
      } else {
        await createMemory({
          content: formContent.trim(),
          type: formType,
          importance: formImportance,
          expires_at: isoExpiry,
        });
      }
      setIsModalOpen(false);
      await loadMemories();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this memory permanently? Its vector representation and encrypted record will be completely expunged.')) {
      return;
    }
    try {
      await deleteMemory(id);
      await loadMemories();
      setDeletionNotice('Memory deleted successfully. Encrypted database record, metadata, and FAISS vector removed.');
      setTimeout(() => setDeletionNotice(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  const handleToggleArchive = async (mem: MemoryItem) => {
    try {
      if (mem.status === 'archived') {
        await updateMemory(mem.id, { status: 'active' });
      } else {
        await archiveMemory(mem.id);
      }
      await loadMemories();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Archive toggle failed');
    }
  };

  const getTypeBadgeColor = (type: string) => {
    switch (type) {
      case 'FACT':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case 'PREFERENCE':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'TASK':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'GOAL':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'CONTEXT':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/40';
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">ReMind</p>
          <h2 className="mt-1 text-3xl font-bold">Personal Context & Memory</h2>
          <p className="text-xs text-slate-400 mt-1">
            Explicit, user-controlled local memory. Never sent to cloud AI or external analytics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={async () => {
              try {
                const res = await cleanupExpiredMemories();
                setDeletionNotice(`Cleaned up ${res.cleaned_up} expired memories.`);
                await loadMemories();
              } catch (err) {
                setError(err instanceof Error ? err.message : 'Cleanup failed');
              }
            }}
            className="rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 px-3 py-2 text-xs font-semibold text-cyan-300 transition"
          >
            Prune Expired
          </button>
          <button
            onClick={openCreateModal}
            className="rounded-lg bg-cyan-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400"
          >
            + Add Memory
          </button>
        </div>
      </header>

      {deletionNotice ? (
        <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-emerald-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span>✓</span>
            <span>{deletionNotice}</span>
          </div>
          <button onClick={() => setDeletionNotice(null)} className="text-emerald-400 hover:text-white text-xs">Dismiss</button>
        </div>
      ) : null}

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      {/* Filter and Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div className="flex flex-wrap items-center gap-2">
          {MEMORY_TYPES.map((t) => (
            <button
              key={t}
              onClick={() => setSelectedType(t)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                selectedType === t
                  ? 'bg-cyan-500 text-slate-950'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 outline-none"
          >
            <option value="active">Active Only</option>
            <option value="archived">Archived</option>
            <option value="all">All Statuses</option>
          </select>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void loadMemories();
            }}
            className="flex items-center"
          >
            <input
              type="text"
              placeholder="Search memories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-200 placeholder:text-slate-500 focus:border-cyan-500 outline-none"
            />
          </form>
        </div>
      </div>

      {/* Memory Cards Grid */}
      {loading ? (
        <div className="py-12 text-center text-slate-400">Loading ReMind local memories...</div>
      ) : memories.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/50 p-12 text-center">
          <span className="text-4xl">🧠</span>
          <h3 className="mt-3 text-lg font-semibold text-slate-200">No memories stored</h3>
          <p className="mt-1 text-sm text-slate-400 max-w-md mx-auto">
            ReMind is not a background surveillance system. It only retains context and memories that you explicitly approve and create.
          </p>
          <button
            onClick={openCreateModal}
            className="mt-4 rounded-lg bg-cyan-500/20 px-4 py-2 text-xs font-semibold text-cyan-300 border border-cyan-500/40 hover:bg-cyan-500/30"
          >
            Add Your First Memory
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {memories.map((mem) => (
            <div
              key={mem.id}
              className={`flex flex-col justify-between rounded-xl border p-4 transition ${
                mem.status === 'archived'
                  ? 'border-slate-800/60 bg-slate-900/40 opacity-70'
                  : mem.status === 'expired'
                  ? 'border-amber-900/40 bg-slate-900/40 opacity-60'
                  : 'border-slate-800 bg-slate-900 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
                  <span
                    className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wider ${getTypeBadgeColor(
                      mem.type
                    )}`}
                  >
                    {mem.type}
                  </span>
                  <div className="flex items-center space-x-1.5 text-[11px]">
                    <span className="text-slate-400">Importance:</span>
                    <span className="font-mono font-medium text-cyan-300">
                      {Math.round((mem.importance ?? 0.5) * 100)}%
                    </span>
                    {mem.status !== 'active' ? (
                      <span className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-slate-400 uppercase">
                        {mem.status}
                      </span>
                    ) : null}
                  </div>
                </div>

                <p className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-slate-100">
                  {mem.content}
                </p>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
                <span title={`Created: ${mem.created_at}`}>
                  {mem.created_at ? new Date(mem.created_at).toLocaleDateString() : 'Local'}
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => openEditModal(mem)}
                    className="hover:text-cyan-300 transition"
                    title="Edit"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleToggleArchive(mem)}
                    className="hover:text-purple-300 transition"
                    title={mem.status === 'archived' ? 'Unarchive' : 'Archive'}
                  >
                    {mem.status === 'archived' ? 'Activate' : 'Archive'}
                  </button>
                  <button
                    onClick={() => handleDelete(mem.id)}
                    className="hover:text-red-400 transition"
                    title="Delete permanently"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Modal */}
      {isModalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-slate-100">
                {editingMemory ? 'Edit Memory' : 'Create Local Memory'}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSave} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Memory Type
                </label>
                <select
                  value={formType}
                  onChange={(e) => setFormType(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2.5 text-sm text-slate-100 outline-none focus:border-cyan-500"
                >
                  <option value="NOTE">NOTE — General note or observation</option>
                  <option value="FACT">FACT — Known verified factual item</option>
                  <option value="PREFERENCE">PREFERENCE — User style or reasoning preference</option>
                  <option value="TASK">TASK — Active todo or objective</option>
                  <option value="GOAL">GOAL — Long-term project milestone</option>
                  <option value="CONTEXT">CONTEXT — Environment or setup state</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Content
                </label>
                <textarea
                  required
                  rows={4}
                  value={formContent}
                  onChange={(e) => setFormContent(e.target.value)}
                  placeholder="Enter memory content..."
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-slate-100 outline-none focus:border-cyan-500"
                />
              </div>

              {/* Real-time Privacy Scan Feedback */}
              {privacyPreview && privacyPreview.entities.length > 0 ? (
                <div
                  className={`rounded-lg p-3 text-xs border ${
                    privacyPreview.allowed
                      ? 'border-amber-500/40 bg-amber-500/10 text-amber-200'
                      : 'border-red-500/40 bg-red-500/10 text-red-200'
                  }`}
                >
                  <div className="flex items-center justify-between font-semibold">
                    <span>
                      {privacyPreview.allowed
                        ? '⚠️ Sensitive Personal Data Detected'
                        : '🛑 Prohibited Credential/Secret Detected'}
                    </span>
                    <span className="text-[10px] uppercase tracking-wider">{privacyPreview.classification}</span>
                  </div>
                  <p className="mt-1 text-[11px] opacity-90">
                    {privacyPreview.allowed
                      ? 'Entities will be protected locally according to privacy policy.'
                      : privacyPreview.block_reason || 'ReMind will block saving credentials into memory.'}
                  </p>
                </div>
              ) : null}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Importance: {Math.round(formImportance * 100)}%
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={formImportance}
                    onChange={(e) => setFormImportance(parseFloat(e.target.value))}
                    className="mt-2 w-full accent-cyan-400"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Expiration Policy
                  </label>
                  <select
                    onChange={(e) => {
                      const val = e.target.value;
                      const now = new Date();
                      if (val === 'never') {
                        setFormExpiresAt('');
                      } else if (val === '7_days') {
                        now.setDate(now.getDate() + 7);
                        setFormExpiresAt(now.toISOString().slice(0, 16));
                      } else if (val === '30_days') {
                        now.setDate(now.getDate() + 30);
                        setFormExpiresAt(now.toISOString().slice(0, 16));
                      } else if (val === '90_days') {
                        now.setDate(now.getDate() + 90);
                        setFormExpiresAt(now.toISOString().slice(0, 16));
                      }
                    }}
                    className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 p-2 text-xs text-slate-200 outline-none focus:border-cyan-500 mb-2"
                  >
                    <option value="never">Never (Persistent)</option>
                    <option value="7_days">7 Days</option>
                    <option value="30_days">30 Days</option>
                    <option value="90_days">90 Days</option>
                    <option value="custom">Custom Date & Time</option>
                  </select>
                  <input
                    type="datetime-local"
                    value={formExpiresAt}
                    onChange={(e) => setFormExpiresAt(e.target.value)}
                    placeholder="Custom ISO timestamp"
                    className="w-full rounded-lg border border-slate-700 bg-slate-950 p-1.5 text-xs text-slate-200 outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              {/* Part 11: Explicit Storage Approval & Summary Review */}
              <div className="rounded-lg border border-slate-800 bg-slate-950/80 p-3.5 space-y-2 text-xs">
                <p className="font-semibold text-slate-300 uppercase tracking-wider text-[11px]">
                  Memory Storage Review & Approval
                </p>
                <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-400 font-mono">
                  <div>
                    <span className="text-slate-500">Storage Protection:</span>{' '}
                    <span className="text-emerald-400">AES-256-GCM + DPAPI</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Classification:</span>{' '}
                    <span className="text-cyan-300">{privacyPreview?.classification || 'PERSONAL'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Importance:</span>{' '}
                    <span className="text-slate-200">{Math.round(formImportance * 100)}%</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Expiration:</span>{' '}
                    <span className="text-slate-200">{formExpiresAt ? new Date(formExpiresAt).toLocaleString() : 'Never expires'}</span>
                  </div>
                </div>
                <label className="flex items-center space-x-2 pt-2 border-t border-slate-800/80 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={userConfirmed}
                    onChange={(e) => setUserConfirmed(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0 accent-cyan-400"
                  />
                  <span className="text-xs text-slate-300 select-none">
                    I explicitly approve storing this memory in ReMind encrypted storage.
                  </span>
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving || !userConfirmed || (privacyPreview !== null && !privacyPreview.allowed)}
                  className="rounded-lg bg-cyan-500 px-5 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-400 disabled:opacity-50"
                >
                  {saving ? 'Encrypting & Storing...' : editingMemory ? 'Save Changes' : 'Confirm & Store Memory'}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}
    </div>
  );
}
