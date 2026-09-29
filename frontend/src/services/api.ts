export const API_BASE_URL =
  (import.meta as ImportMeta & { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL || 'http://localhost:8000';

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}

export async function fetchDocuments() {
  const response = await fetch(`${API_BASE_URL}/api/documents`);
  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }
  return response.json();
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Upload failed');
  }
  return data;
}

export async function deleteDocument(documentId: number) {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
    method: 'DELETE',
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Deletion failed');
  }
  return data;
}

export type SearchSource = {
  document_id: number;
  filename: string;
  page_number: number;
  chunk_id: number;
};

export type SearchMetrics = {
  embedding_latency_seconds?: number;
  search_latency_seconds?: number;
  llm_latency_seconds?: number;
  total_latency_seconds?: number;
  chunks_retrieved?: number;
};

export type SearchResponse = {
  answer: string;
  sources: SearchSource[];
  query: string;
  metrics?: SearchMetrics;
};

export async function searchDocuments(query: string): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Search failed');
  }
  return data;
}
