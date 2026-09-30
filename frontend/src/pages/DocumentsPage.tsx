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
      setUploadMessage(`Successfully ingested & indexed: ${payload.filename} (${payload.status})`);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload error');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  }

  async function handleDelete(documentId: number) {
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
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Documents</p>
          <h2 className="mt-1 text-3xl font-bold">Stored local files</h2>
          <p className="text-xs text-slate-400 mt-1">
            Zero cloud ingestion &bull; AES-256-GCM chunk encryption &bull; FAISS neural vector indexing
          </p>
        </div>
        <label className="cursor-pointer rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950 transition hover:bg-cyan-400">
          <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
          {uploading ? 'Processing PDF...' : 'Upload PDF'}
        </label>
      </header>

      {error ? <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div> : null}
      {uploadMessage ? <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-emerald-200">{uploadMessage}</div> : null}
      {deleteMessage ? <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 p-4 text-cyan-200">{deleteMessage}</div> : null}

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-lg">
        <table className="min-w-full text-left text-sm text-slate-200">
          <thead className="bg-slate-950/70 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800">
            <tr>
              <th className="px-4 py-3">Filename</th>
              <th className="px-4 py-3">Document Type</th>
              <th className="px-4 py-3">Chunks</th>
              <th className="px-4 py-3">Embedding Status</th>
              <th className="px-4 py-3">Index Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-sans">
            {documents.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-12 text-center text-slate-400">
                  <div className="flex flex-col items-center justify-center space-y-2">
                    <span className="text-3xl">📄</span>
                    <p className="font-semibold text-slate-300">No documents indexed yet.</p>
                    <p className="text-xs text-slate-500">
                      Upload a real personal PDF to begin private on-device neural indexing.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-medium text-slate-200 flex items-center gap-2">
                    <span className="text-red-400 text-xs">PDF</span>
                    <span className="truncate max-w-xs">{doc.filename}</span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-400">{doc.mime_type || 'application/pdf'}</td>
                  <td className="px-4 py-3 text-xs font-mono text-cyan-300 font-semibold">{doc.chunk_count ?? '1+'} chunks</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-400 border border-emerald-500/30">
                      {doc.status === 'completed' ? 'INT8 Embedded' : doc.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-2 py-0.5 text-[11px] font-semibold text-cyan-300 border border-cyan-500/30">
                      {doc.status === 'completed' ? 'FAISS Indexed' : 'Processing'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      className="rounded bg-red-500/20 px-2.5 py-1 text-xs font-medium text-red-300 hover:bg-red-500/40 border border-red-500/30 transition"
                      onClick={() => handleDelete(doc.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
