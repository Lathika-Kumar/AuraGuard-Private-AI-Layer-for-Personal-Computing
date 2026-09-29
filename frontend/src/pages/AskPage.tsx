import { FormEvent, useState } from 'react';
import { searchDocuments, SearchSource, SearchMetrics } from '../services/api';

export default function AskPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [sources, setSources] = useState<SearchSource[]>([]);
  const [metrics, setMetrics] = useState<SearchMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState<'retrieving' | 'generating' | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;

    setError(null);
    setAnswer(null);
    setSources([]);
    setMetrics(null);
    setLoading(true);
    setLoadingStage('retrieving');

    // Transition loading stage to indicate pipeline progress
    const timer = setTimeout(() => {
      setLoadingStage('generating');
    }, 400);

    try {
      const payload = await searchDocuments(question.trim());
      setAnswer(payload.answer || "I couldn't find enough relevant information in your local documents.");
      setSources(payload.sources || []);
      setMetrics(payload.metrics || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      clearTimeout(timer);
      setLoading(false);
      setLoadingStage(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Ask AuraGuard</p>
        <h2 className="mt-2 text-3xl font-bold">Local question</h2>
        <p className="mt-1 text-sm text-slate-400">
          Neural on-device question answering grounded in your local documents
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something about your local documents..."
          disabled={loading}
          className="min-h-28 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-slate-100 outline-none ring-0 placeholder:text-slate-500 focus:border-cyan-500/60"
        />
        <div className="flex items-center justify-between">
          <button
            type="submit"
            className="rounded-lg bg-cyan-500 px-5 py-2.5 font-medium text-slate-950 transition hover:bg-cyan-400 disabled:opacity-60"
            disabled={loading || !question.trim()}
          >
            {loading ? 'Processing on-device...' : 'Search local documents'}
          </button>
          {loading ? (
            <div className="flex items-center space-x-2 text-sm text-cyan-400">
              <span className="inline-block h-2 w-2 animate-ping rounded-full bg-cyan-400"></span>
              <span>
                {loadingStage === 'retrieving'
                  ? 'Retrieving local context...'
                  : 'Generating local answer...'}
              </span>
            </div>
          ) : null}
        </div>
      </form>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      {answer ? (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <p className="font-semibold uppercase tracking-wider text-cyan-400">Answer</p>
              {metrics?.total_latency_seconds ? (
                <span className="text-xs text-slate-400">
                  Local execution: {metrics.total_latency_seconds}s
                  {metrics.llm_latency_seconds ? ` (LLM: ${metrics.llm_latency_seconds}s)` : ''}
                </span>
              ) : null}
            </div>
            <p className="mt-4 whitespace-pre-wrap leading-relaxed text-slate-100">{answer}</p>
          </div>

          {sources.length > 0 ? (
            <div className="rounded-xl border border-slate-800 bg-slate-900 p-6">
              <p className="border-b border-slate-800 pb-3 font-semibold uppercase tracking-wider text-cyan-400">
                Sources
              </p>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {sources.map((src, idx) => (
                  <div
                    key={`${src.document_id}-${src.chunk_id}-${idx}`}
                    className="flex flex-col justify-between rounded-lg border border-slate-800 bg-slate-950/70 p-3.5"
                  >
                    <div className="flex items-start space-x-2">
                      <span className="text-base">📄</span>
                      <span className="truncate font-medium text-slate-200" title={src.filename}>
                        {src.filename}
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                      <span className="rounded bg-slate-800 px-2 py-0.5 font-medium text-cyan-300">
                        Page {src.page_number}
                      </span>
                      <span>Chunk #{src.chunk_id}</span>
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
