import { FormEvent, useState } from 'react';

export default function AskPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setAnswer(null);

    try {
      const response = await fetch('http://localhost:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: question }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Search failed');
      }

      setAnswer(payload.answer || "I couldn't find enough relevant information in your local documents.");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Ask AuraGuard</p>
        <h2 className="mt-2 text-3xl font-bold">Local question</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-5">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask something about your local documents..."
          className="min-h-28 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-slate-100 outline-none ring-0 placeholder:text-slate-500"
        />
        <button
          type="submit"
          className="rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950 hover:bg-cyan-400 disabled:opacity-60"
          disabled={!question.trim()}
        >
          Search local documents
        </button>
      </form>

      {error ? <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div> : null}

      {answer ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <p className="font-semibold text-cyan-300">Answer</p>
          <p className="mt-3 text-slate-200">{answer}</p>
        </div>
      ) : null}
    </div>
  );
}
