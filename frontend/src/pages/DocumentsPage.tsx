import { ChangeEvent, useEffect, useState } from 'react';
import { fetchDocuments } from '../services/api';

type DocumentItem = {
  id: number;
  filename: string;
  file_path: string;
  file_hash: string;
  mime_type: string;
  file_size: number;
  created_at: string;
  processed_at: string | null;
  status: string;
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

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
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || 'Upload failed');
      }
      setUploadMessage(`Uploaded: ${payload.filename} (${payload.status})`);
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
      const response = await fetch(`http://localhost:8000/api/documents/${documentId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Delete failed');
      }
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Deletion error');
    }
  }

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Documents</p>
          <h2 className="mt-2 text-3xl font-bold">Stored local files</h2>
        </div>
        <label className="cursor-pointer rounded-lg bg-cyan-500 px-4 py-2 font-medium text-slate-950 transition hover:bg-cyan-400">
          <input type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
          {uploading ? 'Uploading...' : 'Upload PDF'}
        </label>
      </header>

      {error ? <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div> : null}
      {uploadMessage ? <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/10 p-4 text-emerald-200">{uploadMessage}</div> : null}

      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <table className="min-w-full text-left text-sm text-slate-200">
          <thead className="bg-slate-800 text-slate-300">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Size</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                  No documents uploaded yet.
                </td>
              </tr>
            ) : (
              documents.map((doc) => (
                <tr key={doc.id} className="border-t border-slate-800">
                  <td className="px-4 py-3">{doc.filename}</td>
                  <td className="px-4 py-3">
                    <span className="rounded-full bg-slate-800 px-2 py-1 text-xs uppercase tracking-wide">{doc.status}</span>
                  </td>
                  <td className="px-4 py-3">{(doc.file_size / 1024).toFixed(1)} KB</td>
                  <td className="px-4 py-3">{new Date(doc.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3">
                    <button
                      type="button"
                      className="rounded bg-red-500/80 px-2 py-1 text-xs font-medium text-white hover:bg-red-500"
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
