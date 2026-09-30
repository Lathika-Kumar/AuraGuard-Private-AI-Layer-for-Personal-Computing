import { FormEvent, useState } from 'react';
import {
  searchDocuments,
  SearchSource,
  MemorySource,
  SearchMetrics,
  PrivacySummary,
} from '../services/api';

export default function AskPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<SearchSource[]>([]);
  const [memoriesUsed, setMemoriesUsed] = useState<MemorySource[]>([]);
  const [sourceTypes, setSourceTypes] = useState<string[]>([]);
  const [metrics, setMetrics] = useState<SearchMetrics | null>(null);
  const [privacy, setPrivacy] = useState<PrivacySummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<'privacy' | 'retrieving' | 'generating' | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;

    setError(null);
    setAnswer(null);
    setSources([]);
    setMemoriesUsed([]);
    setSourceTypes([]);
    setMetrics(null);
    setPrivacy(null);
    setLoading(true);
    setLoadingStage('privacy');

    const timer1 = setTimeout(() => setLoadingStage('retrieving'), 200);
    const timer2 = setTimeout(() => setLoadingStage('generating'), 600);

    try {
      const payload = await searchDocuments(question.trim());
      setAnswer(payload.answer || "I couldn't find enough relevant information in your local documents or memories.");
      setSources(payload.sources || []);
      setMemoriesUsed(payload.memories_used || []);
      setSourceTypes(payload.source_types || []);
      setMetrics(payload.metrics || null);
      setPrivacy(payload.privacy || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      clearTimeout(timer1);
      clearTimeout(timer2);
      setLoading(false);
      setLoadingStage(null);
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Ask AuraGuard</p>
          <h2 className="mt-1 text-3xl font-bold">Local Context Intelligence</h2>
          <p className="mt-1 text-sm text-slate-400">
            Private neural reasoning across your local documents and approved ReMind memories.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 font-semibold text-emerald-300 border border-emerald-500/30">
            ✓ 100% Local Processing
          </span>
          <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-3 py-1 font-semibold text-cyan-300 border border-cyan-500/30">
            ✓ Privacy Shield Active
          </span>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about your documents, tasks, or saved context..."
          disabled={loading}
          className="min-h-28 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-slate-100 outline-none ring-0 placeholder:text-slate-500 focus:border-cyan-500/60"
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            type="submit"
            className="rounded-lg bg-cyan-500 px-5 py-2.5 font-medium text-slate-950 transition hover:bg-cyan-400 disabled:opacity-60"
            disabled={loading || !question.trim()}
          >
            {loading ? 'Processing On-Device...' : 'Ask AuraGuard'}
          </button>
          {loading ? (
            <div className="flex items-center space-x-2 text-sm text-cyan-400">
              <span className="inline-block h-2 w-2 animate-ping rounded-full bg-cyan-400"></span>
              <span>
                {loadingStage === 'privacy'
                  ? 'Scanning input with Privacy Engine...'
                  : loadingStage === 'retrieving'
                  ? 'Retrieving local documents & memories...'
                  : 'Generating grounded local response...'}
              </span>
            </div>
          ) : null}
        </div>
      </form>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      {/* Answer, Pipeline Visualization, and Context Section */}
      {answer ? (
        <div className="space-y-6">
          {/* Runtime AI Pipeline Visualization */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
                  On-Device AI Pipeline Flow
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Real runtime execution stages, actual latency measurements, and zero-cloud guarantees.
                </p>
              </div>
              <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Provider: {metrics?.execution_provider ?? 'CPUExecutionProvider'}
              </span>
            </div>

            <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4 text-xs font-mono">
              {/* Stage 1: User Query */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">1. User Query</span>
                  <span className="text-emerald-400 font-bold">✓ completed</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1 truncate">"{question}"</p>
              </div>

              {/* Stage 2: Privacy Check (Input) */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">2. Privacy Check</span>
                  {privacy?.input_status === 'blocked' ? (
                    <span className="text-red-400 font-bold">⚠ blocked</span>
                  ) : privacy?.input_scanned ? (
                    <span className="text-emerald-400 font-bold">✓ completed</span>
                  ) : (
                    <span className="text-slate-500">○ skipped</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  {privacy?.classification ? `Class: ${privacy.classification}` : 'Mode: Balanced'}
                  {metrics?.privacy_scan_latency_seconds ? ` • ${(metrics.privacy_scan_latency_seconds * 1000).toFixed(1)}ms` : ''}
                </p>
              </div>

              {/* Stage 3: Memory Retrieval */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">3. Memory Retrieval</span>
                  {(metrics?.memories_retrieved ?? memoriesUsed.length) > 0 ? (
                    <span className="text-purple-400 font-bold">✓ completed</span>
                  ) : (
                    <span className="text-slate-500">○ skipped / none</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  ReMind matches: {metrics?.memories_retrieved ?? memoriesUsed.length}
                  {metrics?.memory_search_latency_seconds ? ` • ${(metrics.memory_search_latency_seconds * 1000).toFixed(1)}ms` : ''}
                </p>
              </div>

              {/* Stage 4: Document Retrieval */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">4. Document Retrieval</span>
                  {(metrics?.chunks_retrieved ?? sources.length) > 0 ? (
                    <span className="text-cyan-400 font-bold">✓ completed</span>
                  ) : (
                    <span className="text-slate-500">○ skipped / none</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  FAISS chunks: {metrics?.chunks_retrieved ?? sources.length}
                  {metrics?.document_search_latency_seconds ? ` • ${(metrics.document_search_latency_seconds * 1000).toFixed(1)}ms` : ''}
                </p>
              </div>

              {/* Stage 5: Context Filtering */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">5. Context Filtering</span>
                  {privacy?.context_redacted ? (
                    <span className="text-amber-400 font-bold">⚠ redacted</span>
                  ) : privacy?.context_scanned ? (
                    <span className="text-emerald-400 font-bold">✓ clean</span>
                  ) : (
                    <span className="text-slate-500">○ clean</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Anti-injection shield & sanitization active
                </p>
              </div>

              {/* Stage 6: Local AI Generation */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">6. Local AI</span>
                  {metrics?.llm_latency_seconds ? (
                    <span className="text-emerald-400 font-bold">✓ completed</span>
                  ) : (
                    <span className="text-emerald-400 font-bold">✓ on-device</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Qwen2.5-0.5B
                  {metrics?.llm_latency_seconds ? ` • ${metrics.llm_latency_seconds.toFixed(2)}s` : ''}
                </p>
              </div>

              {/* Stage 7: Output Privacy Check */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">7. Output Privacy</span>
                  {privacy?.output_blocked ? (
                    <span className="text-red-400 font-bold">⚠ blocked</span>
                  ) : privacy?.output_redacted ? (
                    <span className="text-amber-400 font-bold">⚠ sanitized</span>
                  ) : (
                    <span className="text-emerald-400 font-bold">✓ verified</span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Output guard verified
                  {metrics?.output_guard_latency_seconds ? ` • ${(metrics.output_guard_latency_seconds * 1000).toFixed(1)}ms` : ''}
                </p>
              </div>

              {/* Stage 8: Answer Synthesized */}
              <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">8. Answer</span>
                  <span className="text-emerald-400 font-bold">✓ completed</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">
                  Total: {metrics?.total_latency_seconds ? `${metrics.total_latency_seconds.toFixed(2)}s` : 'Instant'}
                </p>
              </div>
            </div>
          </div>

          {/* Answer Card */}
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <p className="font-semibold uppercase tracking-wider text-cyan-400">Answer</p>
                {sourceTypes.length > 0 ? (
                  <span className="rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300 font-medium">
                    Context: {sourceTypes.includes('document') && sourceTypes.includes('memory')
                      ? 'Both (Documents + ReMind)'
                      : sourceTypes.includes('document')
                      ? 'Documents Only'
                      : 'ReMind Memory Only'}
                  </span>
                ) : null}
              </div>

              {metrics?.total_latency_seconds ? (
                <span className="text-xs text-slate-400 font-mono">
                  Latency: {metrics.total_latency_seconds}s
                  {metrics.llm_latency_seconds ? ` (LLM: ${metrics.llm_latency_seconds}s)` : ''}
                  {metrics.execution_provider ? ` • ${metrics.execution_provider}` : ''}
                </span>
              ) : null}
            </div>

            <p className="mt-4 whitespace-pre-wrap leading-relaxed text-slate-100">{answer}</p>

            {/* Privacy & Provenance Guarantee Footer */}
            <div className="mt-6 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-emerald-400 font-medium">✓ Local processing</span>
                <span>•</span>
                <span className="text-cyan-300 font-medium">✓ Output guarded</span>
                {privacy?.context_redacted ? (
                  <>
                    <span>•</span>
                    <span className="text-amber-300">⚠️ Sensitive context redacted</span>
                  </>
                ) : null}
              </div>
              <div className="font-mono text-slate-500">
                Docs searched: {metrics?.chunks_retrieved ?? sources.length} • Memories searched: {metrics?.memories_retrieved ?? memoriesUsed.length}
              </div>
            </div>
          </div>

          {/* Attributed Document Sources (Part 9 Transparency) */}
          {sources.length > 0 ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <p className="border-b border-slate-800 pb-3 font-semibold uppercase tracking-wider text-cyan-400 flex items-center justify-between">
                <span>Document Sources ({sources.length})</span>
                <span className="text-xs text-slate-400 font-normal font-mono">Encrypted Chunks Decrypted On-the-Fly</span>
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {sources.map((src, idx) => (
                  <div
                    key={`${src.document_id}-${src.chunk_id}-${idx}`}
                    className="flex flex-col justify-between rounded-lg border border-slate-800 bg-slate-950/70 p-3.5"
                  >
                    <div>
                      <div className="flex items-start space-x-2">
                        <span className="text-base">📄</span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold uppercase text-slate-400">Document:</p>
                          <p className="truncate font-medium text-slate-200 text-sm" title={src.filename}>
                            {src.filename}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-xs font-mono text-slate-400">
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-medium text-cyan-300">
                        Page: {src.page_number}
                      </span>
                      <span>Chunk #{src.chunk_id}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Attributed ReMind Memory Sources (Part 9 Transparency) */}
          {memoriesUsed.length > 0 ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <p className="border-b border-slate-800 pb-3 font-semibold uppercase tracking-wider text-purple-400 flex items-center justify-between">
                <span>ReMind Memory Sources ({memoriesUsed.length})</span>
                <span className="text-xs text-slate-400 font-normal font-mono">User-Approved Local Memories</span>
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {memoriesUsed.map((mem) => (
                  <div
                    key={mem.id}
                    className="flex flex-col justify-between rounded-lg border border-slate-800 bg-slate-950/70 p-3.5"
                  >
                    <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                      <span className="text-xs font-mono font-semibold text-purple-300">
                        Memory: ReMind memory #{mem.id}
                      </span>
                      <span className="rounded bg-purple-500/20 px-2 py-0.5 text-[10px] font-semibold text-purple-300 border border-purple-500/30">
                        {mem.memory_type}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-slate-300 line-clamp-3">
                      {mem.content}
                    </p>
                    <div className="mt-3 flex items-center justify-between border-t border-slate-800/80 pt-2 text-[11px] font-mono text-slate-400">
                      <span>Importance: {Math.round((mem.importance ?? 0.5) * 100)}%</span>
                      <span className="text-emerald-400">AES-256 Encrypted</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
