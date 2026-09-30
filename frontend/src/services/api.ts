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
  text?: string;
  score?: number;
  sensitivity?: string;
};

export type MemorySource = {
  id: number;
  memory_type: string;
  content: string;
  importance: number;
  score?: number;
  sensitivity?: string;
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

export type DecisionResult = {
  processing_mode: string;
  privacy_mode: string;
  sensitivity: string;
  user_intent: string;
  memory_allowed: boolean;
  retrieval_allowed: boolean;
  sensitive_data_detected: boolean;
  execution_provider: string;
  fallback_active: boolean;
  network_policy: string;
  model_id: string;
  reason: string;
  allowed: boolean;
  block_reason?: string | null;
};

export type FirewallEvent = {
  category: string;
  reason: string;
  action: string;
  source: string;
};

export type TransparencyReport = {
  model: string;
  execution_provider: string;
  processing_mode: string;
  network_policy: string;
  sensitivity: string;
  user_intent: string;
  sources_count: number;
  memories_count: number;
  privacy_checks: {
    input: string;
    context: string;
    output: string;
  };
  firewall_events: FirewallEvent[];
  runtime_rationale: string;
};

export type MemoryCandidate = {
  content: string;
  memory_type: string;
  sensitivity: string;
  reason: string;
  requires_user_approval: boolean;
};

export type SearchResponse = {
  answer: string;
  sources: SearchSource[];
  memories_used: MemorySource[];
  source_types: string[];
  query: string;
  privacy: PrivacySummary;
  metrics: SearchMetrics;
  ai_runtime: any;
  decision?: DecisionResult;
  transparency?: TransparencyReport;
  memory_candidate?: MemoryCandidate | null;
  firewall_events?: FirewallEvent[];
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

export type UserPolicy = {
  id?: number;
  privacy_mode: 'strict' | 'balanced' | 'permissive' | string;
  local_processing: string;
  external_ai: string;
  memory_mode: string;
  sensitive_data_action: string;
  document_retrieval: string;
  automatic_memory: string;
  updated_at?: string;
};

export type PrivacyPolicyInfo = {
  mode: string;
  privacy_mode?: string;
  policy?: UserPolicy;
  available_modes: string[];
  rules: Record<string, any>;
};

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

export async function updateUserPolicy(updates: Partial<UserPolicy>): Promise<{ status: string; mode: string; policy: UserPolicy }> {
  const response = await fetch(`${API_BASE_URL}/api/privacy/policy`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to update privacy policy');
  }
  return data;
}

export async function cleanupExpiredMemories(): Promise<{ status: string; cleaned_up: number }> {
  const response = await fetch(`${API_BASE_URL}/api/memories/cleanup-expired`, {
    method: 'POST',
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || 'Failed to cleanup expired memories');
  }
  return data;
}

export async function fetchPrivacyLedger(limit: number = 50, eventType?: string): Promise<PrivacyEvent[]> {
  const query = new URLSearchParams();
  query.append('limit', limit.toString());
  if (eventType) query.append('event_type', eventType);
  const response = await fetch(`${API_BASE_URL}/api/privacy/ledger?${query.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to fetch privacy ledger');
  }
  return response.json();
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
  local_ai?: string;
  cloud_inference?: string;
  privacy_events?: number;
  blocked_requests?: number;
  encrypted_memories?: number;
  encrypted_documents?: number;
};

export async function fetchSecurityStatus(): Promise<SecurityStatus> {
  const response = await fetch(`${API_BASE_URL}/api/system/security`);
  if (!response.ok) {
    throw new Error('Failed to fetch security status');
  }
  return response.json();
}

export type AIRuntimeVerifyResult = {
  hardware_detected: boolean;
  qnn_installed?: boolean;
  qnn_available: boolean;
  provider_loaded: boolean;
  model_loaded: boolean;
  inference_verified: boolean;
  active_fallback?: string | null;
  error_reason?: string | null;
};

export async function verifyAIRuntime(): Promise<AIRuntimeVerifyResult> {
  const response = await fetch(`${API_BASE_URL}/api/system/ai-runtime/verify`);
  if (!response.ok) {
    throw new Error('Failed to verify AI runtime');
  }
  return response.json();
}
