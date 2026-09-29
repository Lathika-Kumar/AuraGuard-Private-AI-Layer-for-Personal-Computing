import { useEffect, useState } from 'react';
import { fetchHealth, fetchDocuments, fetchHardware, fetchAIRuntime, HardwareInfo, AIRuntimeInfo } from '../services/api';

export default function DashboardPage() {
  const [health, setHealth] = useState<{ status?: string; python_version?: string } | null>(null);
  const [docs, setDocs] = useState<Array<{ id: number }>>([]);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [aiRuntime, setAiRuntime] = useState<AIRuntimeInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [healthResponse, documentsResponse, hwResponse, runtimeResponse] = await Promise.all([
          fetchHealth(),
          fetchDocuments(),
          fetchHardware(),
          fetchAIRuntime(),
        ]);
        setHealth(healthResponse);
        setDocs(documentsResponse);
        setHardware(hwResponse);
        setAiRuntime(runtimeResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data.');
      }
    }
    void load();
  }, []);

  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Dashboard</p>
          <h2 className="mt-2 text-3xl font-bold">System overview</h2>
        </div>
      </header>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Documents indexed" value={docs.length} />
        <StatCard label="Memories stored" value={0} />
        <StatCard label="Privacy events" value={0} />
      </div>

      {/* AI Runtime & Snapdragon Acceleration Status */}
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
            {aiRuntime?.npu_available ? 'NPU Accelerated' : 'CPU Execution (Fallback Active)'}
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
              {aiRuntime?.npu_available ? 'Hexagon NPU Active' : 'Not Present (Graceful CPU Fallback)'}
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

        <div className="mt-4 rounded-lg bg-slate-950/70 p-3 text-xs text-slate-400 border border-slate-800/60">
          <span className="font-semibold text-slate-300">Runtime Telemetry: </span>
          {aiRuntime?.status_reason ?? 'Hardware acceleration pipeline initialized.'}
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

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-cyan-300">{value}</p>
    </div>
  );
}
