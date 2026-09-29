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
  execution_provider?: string;
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
  query: string;
  metrics?: SearchMetrics;
  ai_runtime?: AIRuntimeInfo;
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
