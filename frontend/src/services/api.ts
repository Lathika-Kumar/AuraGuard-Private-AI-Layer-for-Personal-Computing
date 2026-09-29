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

export type MemorySource = {
  id: number;
  memory_type: string;
  content: string;
  importance: number;
  score?: number;
};

export type SearchMetrics = {
  privacy_scan_latency_seconds?: number;
  embedding_latency_seconds?: number;
  document_search_latency_seconds?: number;
  memory_search_latency_seconds?: number;
  context_merging_latency_seconds?: number;
  llm_latency_seconds?: number;
  output_guard_latency_seconds?: number;
  total_latency_seconds?: number;
  chunks_retrieved?: number;
  memories_retrieved?: number;
  execution_provider?: string;
};

export type PrivacySummary = {
  input_scanned?: boolean;
  input_status?: string;
  classification?: string;
  context_scanned?: boolean;
  context_redacted?: boolean;
  output_guarded?: boolean;
  output_redacted?: boolean;
  output_blocked?: boolean;
  local_guarantee?: boolean;
  policy_mode?: string;
  blocked_reason?: string;
};

export type HardwareInfo = {
  os: {
    system: string;
    release: string;
    version: string;
    platform: string;
  };
  cpu: {
    brand: string;
    architecture: string;
    physical_cores: number;
    logical_cores: number;
  };
  gpu: {
    name: string;
  };
  memory: {
    total_bytes: number;
    total_gb: number;
    available_bytes: number;
    available_gb: number;
    percent_used: number;
  };
  snapdragon: {
    is_snapdragon: boolean;
    processor_detected: string | null;
    target_device: string;
  };
  npu: {
    npu_available: boolean;
    npu_type: string;
    acceleration_active: boolean;
  };
};

export type AIRuntimeInfo = {
  runtime_status: string;
  active_execution_provider: string;
  configured_execution_provider: string;
  fallback_occurred: boolean;
  status_reason: string;
  available_execution_providers: string[];
  qnn_available: boolean;
  snapdragon_hardware: boolean;
  npu_available: boolean;
  models: {
    embedding: {
      model_name: string;
      runtime: string;
      execution_provider: string;
      dimension: number;
      precision: string;
      device: string;
    };
    llm: {
      model_id: string;
      runtime: string;
      execution_provider: string;
      device: string;
      precision: string;
      max_new_tokens: number;
    };
  };
  qualcomm_ai_hub: {
    target_architecture: string;
    toolchain: string;
    compilation_targets: string[];
    status: string;
  };
};

export type SearchResponse = {
  answer: string;
  sources: SearchSource[];
  memories_used?: MemorySource[];
  source_types?: string[];
  query: string;
  privacy?: PrivacySummary;
  metrics?: SearchMetrics;
  ai_runtime?: AIRuntimeInfo;
};

export async function searchDocuments(
  query: string,
  options?: { top_k_docs?: number; top_k_memories?: number; policy_mode?: string }
): Promise<SearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/search`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      top_k_docs: options?.top_k_docs ?? 4,
      top_k_memories: options?.top_k_memories ?? 3,
      policy_mode: options?.policy_mode,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Search failed');
  }
  return data;
}

export async function fetchHardware(): Promise<HardwareInfo> {
  const response = await fetch(`${API_BASE_URL}/api/system/hardware`);
  if (!response.ok) {
    throw new Error('Failed to fetch system hardware information');
  }
  return response.json();
}

export async function fetchAIRuntime(): Promise<AIRuntimeInfo> {
  const response = await fetch(`${API_BASE_URL}/api/system/ai-runtime`);
  if (!response.ok) {
    throw new Error('Failed to fetch AI runtime information');
  }
  return response.json();
}

export type ModelDetail = {
  name: string;
  runtime: string;
  precision: string;
  provider: string;
};

export type SystemModelsResponse = {
  embedding: ModelDetail;
  llm: ModelDetail;
};

export async function fetchSystemModels(): Promise<SystemModelsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/system/models`);
  if (!response.ok) {
    throw new Error('Failed to fetch system models');
  }
  return response.json();
}

export type DashboardStats = {
  documents_indexed: number;
  memories_stored: number;
  privacy_events: number;
  privacy_mode: string;
  active_execution_provider: string;
  qnn_available: boolean;
  external_calls: number;
};

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/api/system/dashboard-stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch dashboard statistics');
  }
  return response.json();
}

// ==========================================
// ReMind Memory Service API
// ==========================================

export type MemoryItem = {
  id: number;
  type: 'FACT' | 'PREFERENCE' | 'TASK' | 'GOAL' | 'NOTE' | 'CONTEXT' | string;
  content: string;
  source: string;
  importance: number;
  confidence: number;
  privacy_level: string;
  created_at: string;
  updated_at?: string;
  expires_at?: string | null;
  status: 'active' | 'archived' | 'expired' | string;
  score?: number;
};

export type CreateMemoryPayload = {
  content: string;
  type: string;
  importance?: number;
  confidence?: number;
  expires_at?: string | null;
  source?: string;
};

export type UpdateMemoryPayload = {
  content?: string;
  type?: string;
  importance?: number;
  confidence?: number;
  expires_at?: string | null;
  status?: string;
};

export async function fetchMemories(params?: {
  type?: string;
  status?: string;
  search?: string;
  include_expired?: boolean;
}): Promise<MemoryItem[]> {
  const query = new URLSearchParams();
  if (params?.type) query.append('type', params.type);
  if (params?.status) query.append('status', params.status);
  if (params?.search) query.append('search', params.search);
  if (params?.include_expired) query.append('include_expired', 'true');

  const url = `${API_BASE_URL}/api/memories${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch memories');
  }
  return response.json();
}

export async function createMemory(payload: CreateMemoryPayload): Promise<MemoryItem> {
  const response = await fetch(`${API_BASE_URL}/api/memories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to create memory');
  }
  return data;
}

export async function updateMemory(id: number, payload: UpdateMemoryPayload): Promise<MemoryItem> {
  const response = await fetch(`${API_BASE_URL}/api/memories/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to update memory');
  }
  return data;
}

export async function deleteMemory(id: number): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/api/memories/${id}`, {
    method: 'DELETE',
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to delete memory');
  }
  return data;
}

export async function archiveMemory(id: number): Promise<MemoryItem> {
  const response = await fetch(`${API_BASE_URL}/api/memories/${id}/archive`, {
    method: 'POST',
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to archive memory');
  }
  return data;
}

// ==========================================
// Privacy Engine Service API
// ==========================================

export type PrivacyEntity = {
  type: string;
  text: string;
  start: number;
  end: number;
  classification: string;
  action: string;
  confidence: number;
};

export type PrivacyAnalysis = {
  classification: string;
  entities: PrivacyEntity[];
  allowed: boolean;
  policy_mode: string;
  redacted_text: string;
  block_reason?: string | null;
};

export type PrivacyEvent = {
  id: number;
  event_type: string;
  severity: string;
  source: string;
  description: string;
  entity_type?: string | null;
  action?: string | null;
  created_at: string;
  resolved: number;
};

export type PrivacyStats = {
  total_events: number;
  blocked_events: number;
  redacted_events: number;
  entity_breakdown: Record<string, number>;
  policy_mode: string;
  local_processing: string;
  external_network_calls: number;
};

export type PrivacyPolicyInfo = {
  mode: string;
  available_modes: string[];
  rules: Record<string, any>;
};

export async function analyzePrivacy(text: string, mode?: string): Promise<PrivacyAnalysis> {
  const response = await fetch(`${API_BASE_URL}/api/privacy/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, mode }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Privacy analysis failed');
  }
  return data;
}

export async function fetchPrivacyEvents(limit: number = 50, offset: number = 0): Promise<PrivacyEvent[]> {
  const response = await fetch(`${API_BASE_URL}/api/privacy/events?limit=${limit}&offset=${offset}`);
  if (!response.ok) {
    throw new Error('Failed to fetch privacy events');
  }
  return response.json();
}

export async function fetchPrivacyStats(): Promise<PrivacyStats> {
  const response = await fetch(`${API_BASE_URL}/api/privacy/stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch privacy stats');
  }
  return response.json();
}

export async function fetchPrivacyPolicy(): Promise<PrivacyPolicyInfo> {
  const response = await fetch(`${API_BASE_URL}/api/privacy/policy`);
  if (!response.ok) {
    throw new Error('Failed to fetch privacy policy');
  }
  return response.json();
}

export async function updatePrivacyPolicy(mode: string): Promise<{ status: string; mode: string }> {
  const response = await fetch(`${API_BASE_URL}/api/privacy/policy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mode }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to update privacy policy');
  }
  return data;
}

export type SecurityStatus = {
  storage_encryption: boolean;
  algorithm: string;
  key_length_bits: number;
  key_protection: string;
  database_encrypted: boolean;
  memory_encrypted: boolean;
  documents_encrypted: boolean;
  faiss_protection: string;
  local_only: boolean;
  cloud_leakage: boolean;
};

export async function fetchSecurityStatus(): Promise<SecurityStatus> {
  const response = await fetch(`${API_BASE_URL}/api/system/security`);
  if (!response.ok) {
    throw new Error('Failed to fetch security status');
  }
  return response.json();
}
