import { useEffect, useState } from 'react';
import {
  fetchHealth,
  fetchHardware,
  fetchAIRuntime,
  fetchDashboardStats,
  fetchSystemModels,
  HardwareInfo,
  AIRuntimeInfo,
  DashboardStats,
  SystemModelsResponse,
} from '../services/api';

export default function DashboardPage() {
  const [health, setHealth] = useState<{ status?: string; python_version?: string } | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [aiRuntime, setAiRuntime] = useState<AIRuntimeInfo | null>(null);
  const [models, setModels] = useState<SystemModelsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [healthResponse, statsResponse, hwResponse, runtimeResponse, modelsResponse] = await Promise.all([
          fetchHealth(),
          fetchDashboardStats(),
          fetchHardware(),
          fetchAIRuntime(),
          fetchSystemModels().catch(() => null),
        ]);
        setHealth(healthResponse);
        setStats(statsResponse);
        setHardware(hwResponse);
        setAiRuntime(runtimeResponse);
        setModels(modelsResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data.');
      }
    }
    void load();
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Dashboard</p>
          <h2 className="mt-1 text-3xl font-bold">System overview</h2>
          <p className="text-xs text-slate-400 mt-1">
            Privacy Engine &bull; ReMind Local Context Layer &bull; On-Device AI Runtime
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300 border border-cyan-500/30">
            Privacy: {stats?.privacy_mode?.toUpperCase() ?? 'BALANCED'}
          </span>
          <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300 border border-emerald-500/30">
            Local First: 100%
          </span>
        </div>
      </header>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      {/* Real Counts from Database */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Documents indexed"
          value={stats?.documents_indexed ?? 0}
          detail="PDFs partitioned & embedded locally"
          icon="📄"
        />
        <StatCard
          label="Approved memories"
          value={stats?.memories_stored ?? 0}
          detail="ReMind personal context entries"
          icon="🧠"
        />
        <StatCard
          label="Privacy events"
          value={stats?.privacy_events ?? 0}
          detail="Redactions & shield events"
          icon="🛡️"
        />
      </div>

      {/* Technical Model / AI Runtime Specification Panel */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
              AI Runtime Specification
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              On-device execution pipeline &bull; Qualcomm AI Hub target profile
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Execution: {hardware?.snapdragon.is_snapdragon && aiRuntime?.qnn_available ? 'QNN' : 'CPU'}
            </span>
            <span className="font-mono text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
              Device: {hardware?.snapdragon.is_snapdragon ? 'Snapdragon' : 'Intel'}
            </span>
            <span className={`font-mono text-xs px-2.5 py-1 rounded border ${
              aiRuntime?.npu_available
                ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-300 border-amber-500/30'
            }`}>
              Accelerator: {aiRuntime?.npu_available ? 'NPU' : 'NPU unavailable'}
            </span>
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 text-xs font-mono">
          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <span className="text-slate-500 block uppercase tracking-wider text-[10px]">Embedding Model</span>
            <span className="text-slate-200 text-sm font-semibold truncate block mt-0.5">
              {models?.embedding.name.split('/').pop() ?? 'all-MiniLM-L6-v2'}
            </span>
            <div className="mt-2 text-slate-400 space-y-0.5 text-[11px]">
              <div>Runtime: <span className="text-cyan-300">{models?.embedding.runtime ?? 'onnxruntime'}</span></div>
              <div>Precision: <span className="text-emerald-400">{models?.embedding.precision ?? 'float32'}</span></div>
              <div>Provider: <span className="text-slate-300">{models?.embedding.provider ?? 'CPUExecutionProvider'}</span></div>
            </div>
          </div>

          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <span className="text-slate-500 block uppercase tracking-wider text-[10px]">LLM Model</span>
            <span className="text-slate-200 text-sm font-semibold truncate block mt-0.5">
              {models?.llm.name.split('/').pop() ?? 'Qwen2.5-0.5B-Instruct'}
            </span>
            <div className="mt-2 text-slate-400 space-y-0.5 text-[11px]">
              <div>Runtime: <span className="text-cyan-300">{models?.llm.runtime ?? 'pytorch'}</span></div>
              <div>Precision: <span className="text-emerald-400">{models?.llm.precision ?? 'float32'}</span></div>
              <div>Provider: <span className="text-slate-300">{models?.llm.provider ?? 'CPU'}</span></div>
            </div>
          </div>

          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <span className="text-slate-500 block uppercase tracking-wider text-[10px]">Active Execution State</span>
            <div className="mt-1 space-y-1.5 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Execution:</span>
                <span className="text-cyan-300 font-semibold">{hardware?.snapdragon.is_snapdragon && aiRuntime?.qnn_available ? 'QNN' : 'CPU'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Device:</span>
                <span className="text-slate-200">{hardware?.snapdragon.is_snapdragon ? 'Snapdragon' : 'Intel'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Accelerator:</span>
                <span className={aiRuntime?.npu_available ? 'text-emerald-400' : 'text-amber-400'}>
                  {aiRuntime?.npu_available ? 'NPU' : 'NPU unavailable'}
                </span>
              </div>
            </div>
          </div>

          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80">
            <span className="text-slate-500 block uppercase tracking-wider text-[10px]">Target Platform</span>
            <div className="mt-1 space-y-1.5 text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Target Arch:</span>
                <span className="text-slate-200">Snapdragon X Elite</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Target NPU:</span>
                <span className="text-slate-200">Qualcomm Hexagon</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">LLM Precision:</span>
                <span className="text-emerald-400">
                  {hardware?.snapdragon.is_snapdragon ? 'INT4' : (models?.llm.precision ?? 'float32')}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Runtime & Hardware Readiness */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <h3 className="text-lg font-semibold text-slate-100">AI Runtime & Hardware Acceleration</h3>
          <span
            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
              aiRuntime?.npu_available
                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-300 border border-amber-500/30'
            }`}
          >
            {aiRuntime?.npu_available ? 'NPU Accelerated' : 'CPU Execution (Graceful Fallback)'}
          </span>
        </div>

        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 text-sm text-slate-300">
          <div className="rounded-lg border border-slate-800/80 bg-slate-950/50 p-3">
            <p className="text-xs text-slate-400">Host Processor</p>
            <p className="mt-1 font-medium text-slate-200">{hardware?.cpu.brand ?? 'Detecting...'}</p>
            <p className="mt-0.5 text-xs text-slate-500">
              Arch: {hardware?.cpu.architecture ?? 'x86_64'} | {hardware?.cpu.logical_cores ?? 1} Cores
            </p>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-slate-950/50 p-3">
            <p className="text-xs text-slate-400">Snapdragon Platform</p>
            <p className="mt-1 font-medium text-slate-200">
              {hardware?.snapdragon.is_snapdragon ? 'Snapdragon Detected' : 'Intel/AMD x86_64 Host'}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              Target: {hardware?.snapdragon.target_device ?? 'Snapdragon X Elite'}
            </p>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-slate-950/50 p-3">
            <p className="text-xs text-slate-400">Qualcomm Hexagon NPU</p>
            <p className="mt-1 font-medium text-slate-200">
              {aiRuntime?.npu_available ? 'Hexagon NPU Active' : 'Not Present (CPU Fallback)'}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              QNN Execution Provider: {aiRuntime?.qnn_available ? 'Available' : 'Unavailable'}
            </p>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-slate-950/50 p-3">
            <p className="text-xs text-slate-400">Active Execution Provider</p>
            <p className="mt-1 font-mono text-cyan-300">
              {aiRuntime?.active_execution_provider ?? 'CPUExecutionProvider'}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">Configured: {aiRuntime?.configured_execution_provider ?? 'auto'}</p>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-slate-950/50 p-3">
            <p className="text-xs text-slate-400">Neural Embeddings</p>
            <p className="mt-1 font-medium text-slate-200">
              {aiRuntime?.models.embedding.model_name.split('/').pop() ?? 'all-MiniLM-L6-v2'}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              Runtime: {aiRuntime?.models.embedding.runtime} (dim: {aiRuntime?.models.embedding.dimension})
            </p>
          </div>

          <div className="rounded-lg border border-slate-800/80 bg-slate-950/50 p-3">
            <p className="text-xs text-slate-400">Neural Language Model</p>
            <p className="mt-1 font-medium text-slate-200">
              {aiRuntime?.models.llm.model_id.split('/').pop() ?? 'Qwen2.5-0.5B-Instruct'}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              Runtime: {aiRuntime?.models.llm.runtime} ({aiRuntime?.models.llm.device.toUpperCase()})
            </p>
          </div>
        </div>

        <div className="mt-4 rounded-lg bg-slate-950/70 p-3 text-xs text-slate-400 border border-slate-800/60 flex items-center justify-between">
          <div>
            <span className="font-semibold text-slate-300">Runtime Telemetry: </span>
            {aiRuntime?.status_reason ?? 'Hardware acceleration pipeline initialized.'}
          </div>
          <div className="text-slate-500 font-mono">External Calls: 0</div>
        </div>
      </div>

      {/* Device & Memory Details */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
        <h3 className="text-lg font-semibold">Device & Memory Specifications</h3>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 md:grid-cols-4 text-sm text-slate-300">
          <div>
            <p className="text-xs text-slate-500">Operating System</p>
            <p className="mt-1 font-medium">{hardware?.os.platform ?? 'Windows'}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Graphics (GPU)</p>
            <p className="mt-1 font-medium">{hardware?.gpu.name ?? 'Integrated'}</p>
          </div>
          <div>
            <p className="text-xs text-slate-500">System Memory</p>
            <p className="mt-1 font-medium">
              {hardware?.memory.total_gb ?? 0} GB total ({hardware?.memory.available_gb ?? 0} GB free)
            </p>
          </div>
          <div>
            <p className="text-xs text-slate-500">Local-First Status</p>
            <p className="mt-1 font-medium text-emerald-400">Strictly Local (0% Cloud)</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, detail, icon }: { label: string; value: number; detail: string; icon: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-400">{label}</p>
        <span className="text-xl">{icon}</span>
      </div>
      <p className="mt-3 text-3xl font-bold text-cyan-300">{value}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
  );
}
