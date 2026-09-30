import { ChangeEvent, useEffect, useState } from 'react';
import { fetchDocuments, uploadDocument, deleteDocument } from '../services/api';

type DocumentItem = {
  id: number;
  filename: string;
  file_path: string;
  file_hash: string;
  mime_type: string;
  file_size: number;
  chunk_count?: number;
  created_at: string;
  processed_at: string | null;
  status: string;
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-400 border border-emerald-500/30">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        Indexed
      </span>
    );
  }
  if (status === 'processing') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[11px] font-semibold text-amber-400 border border-amber-500/30">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
        Processing
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-slate-800 px-2 py-0.5 text-[11px] font-semibold text-slate-400 border border-slate-700">
      {status}
    </span>
  );
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [deleteMessage, setDeleteMessage] = useState<string | null>(null);

  async function loadDocuments() {
    try {
      const data = await fetchDocuments();
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load documents.');
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, []);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadMessage(null);
    setDeleteMessage(null);
    setError(null);

    try {
      const payload = await uploadDocument(file);
      setUploadMessage(`✓ Ingested & indexed: ${payload.filename} — ${payload.status}`);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload error');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  }

  async function handleDelete(documentId: number) {
    if (!window.confirm('Delete this document, its encrypted chunks, and FAISS vectors permanently?')) return;
    try {
      setDeleteMessage(null);
      setError(null);
      await deleteDocument(documentId);
      setDeleteMessage('Document, encrypted chunk records, and FAISS vector mappings permanently removed.');
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deletion error');
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Documents</p>
          <h2 className="mt-1 text-3xl font-bold">Local Document Library</h2>
          <p className="text-xs text-slate-400 mt-1">
            Zero cloud ingestion · AES-256-GCM chunk encryption · FAISS neural vector indexing
          </p>
        </div>
        <label
          id="upload-pdf-btn"
          className={`cursor-pointer rounded-lg px-4 py-2.5 font-medium text-slate-950 transition-all shadow-md ${
            uploading
              ? 'bg-cyan-400/60 cursor-not-allowed'
              : 'bg-cyan-400 hover:bg-cyan-300 hover:shadow-cyan-500/30'
          }`}
        >
          <input
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={handleUpload}
            disabled={uploading}
          />
          {uploading ? (
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-full border-2 border-slate-950/40 border-t-slate-950 animate-spin" />
              Processing PDF…
            </span>
          ) : (
            '+ Upload PDF'
          )}
        </label>
      </header>

      {/* Notices */}
      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200 flex items-start gap-2">
          <span>⚠</span> {error}
        </div>
      ) : null}
      {uploadMessage ? (
        <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-emerald-200 flex items-start gap-2">
          <span>✓</span> {uploadMessage}
        </div>
      ) : null}
      {deleteMessage ? (
        <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 p-4 text-cyan-200 flex items-start gap-2">
          <span>🗑</span> {deleteMessage}
        </div>
      ) : null}

      {/* Pipeline explanation banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 px-5 py-3 text-xs text-slate-400 flex flex-wrap items-center gap-3">
        <span className="text-slate-300 font-semibold">Ingestion pipeline:</span>
        {['PDF Parse', 'Page-Aware Chunking', 'ONNX INT8 Embedding', 'AES-256-GCM Encryption', 'FAISS FlatL2 Index'].map((step, i, arr) => (
          <span key={step} className="flex items-center gap-1.5">
            <span className="font-mono text-cyan-400">{step}</span>
            {i < arr.length - 1 ? <span className="text-slate-700">→</span> : null}
          </span>
        ))}
      </div>

      {/* Document table */}
      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-lg">
        {documents.length === 0 ? (
          /* Empty state */
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <div className="h-16 w-16 rounded-2xl bg-slate-800 border border-slate-700 flex items-center justify-center text-3xl">
              📄
            </div>
            <div className="text-center">
              <p className="font-semibold text-slate-200 text-base">No documents indexed yet</p>
              <p className="text-sm text-slate-500 mt-1">
                Upload a real personal PDF to begin private on-device neural indexing.
              </p>
              <p className="text-xs text-slate-600 mt-1">
                Use openly licensed documents for the demo (e.g., public research papers, technical documentation).
              </p>
            </div>
            <label className="cursor-pointer rounded-lg bg-cyan-500/20 border border-cyan-500/40 px-4 py-2 text-sm font-semibold text-cyan-300 hover:bg-cyan-500/30 transition">
              <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
              Choose a PDF to upload
            </label>
          </div>
        ) : (
          <table className="min-w-full text-left text-sm text-slate-200">
            <thead className="bg-slate-950/70 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
              <tr>
                <th className="px-5 py-3.5">Filename</th>
                <th className="px-5 py-3.5">Size</th>
                <th className="px-5 py-3.5 text-center">Chunks</th>
                <th className="px-5 py-3.5 text-center">Status</th>
                <th className="px-5 py-3.5 text-center">Index</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-800/20 transition-colors">
                  <td className="px-5 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <span className="flex-shrink-0 rounded bg-red-500/20 border border-red-500/30 px-1.5 py-0.5 text-[10px] font-bold text-red-300 uppercase">
                        PDF
                      </span>
                      <span className="truncate max-w-xs font-medium text-slate-200" title={doc.filename}>
                        {doc.filename}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-3.5 text-xs font-mono text-slate-400">
                    {formatBytes(doc.file_size)}
                  </td>
                  <td className="px-5 py-3.5 text-center text-xs font-mono text-cyan-300 font-semibold">
                    {doc.chunk_count ?? '—'}
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    <StatusBadge status={doc.status} />
                  </td>
                  <td className="px-5 py-3.5 text-center">
                    {doc.status === 'completed' ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-cyan-500/10 px-2 py-0.5 text-[11px] font-semibold text-cyan-300 border border-cyan-500/30">
                        FAISS Indexed
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-500 font-mono">—</span>
                    )}
                  </td>
                  <td className="px-5 py-3.5 text-right">
                    <button
                      type="button"
                      id={`delete-doc-${doc.id}`}
                      className="rounded-md bg-red-500/10 px-3 py-1.5 text-xs font-medium text-red-400 hover:bg-red-500/25 border border-red-500/20 hover:border-red-500/40 transition"
                      onClick={() => handleDelete(doc.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t border-slate-800 bg-slate-950/40">
              <tr>
                <td colSpan={6} className="px-5 py-2.5 text-xs text-slate-500 font-mono">
                  {documents.length} document{documents.length !== 1 ? 's' : ''} · All chunks encrypted AES-256-GCM at rest · Zero cloud egress
                </td>
              </tr>
            </tfoot>
          </table>
        )}
      </div>
    </div>
  );
}
