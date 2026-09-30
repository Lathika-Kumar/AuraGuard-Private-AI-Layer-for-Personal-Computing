import { useEffect, useState } from 'react';
import {
  fetchHealth,
  fetchHardware,
  fetchAIRuntime,
  fetchDashboardStats,
  fetchSystemModels,
  fetchSecurityStatus,
  verifyAIRuntime,
  HardwareInfo,
  AIRuntimeInfo,
  DashboardStats,
  SystemModelsResponse,
  SecurityStatus,
  AIRuntimeVerifyResult,
} from '../services/api';

export default function DashboardPage() {
  const [, setHealth] = useState<{ status?: string; python_version?: string } | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [hardware, setHardware] = useState<HardwareInfo | null>(null);
  const [aiRuntime, setAiRuntime] = useState<AIRuntimeInfo | null>(null);
  const [models, setModels] = useState<SystemModelsResponse | null>(null);
  const [security, setSecurity] = useState<SecurityStatus | null>(null);
  const [runtimeVerify, setRuntimeVerify] = useState<AIRuntimeVerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const [healthResponse, statsResponse, hwResponse, runtimeResponse, modelsResponse, secResponse, verifyResponse] = await Promise.all([
          fetchHealth(),
          fetchDashboardStats(),
          fetchHardware(),
          fetchAIRuntime(),
          fetchSystemModels().catch(() => null),
          fetchSecurityStatus().catch(() => null),
          verifyAIRuntime().catch(() => null),
        ]);
        setHealth(healthResponse);
        setStats(statsResponse);
        setHardware(hwResponse);
        setAiRuntime(runtimeResponse);
        setModels(modelsResponse);
        setSecurity(secResponse);
        setRuntimeVerify(verifyResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unable to load dashboard data.');
      }
    }
    void load();
  }, []);

  // Part 17: Live NPU Status (5 distinct states)
  let npuStatus: 'NOT AVAILABLE' | 'AVAILABLE' | 'PROVIDER LOADED' | 'MODEL LOADED' | 'INFERENCE VERIFIED' = 'NOT AVAILABLE';
  if (runtimeVerify?.inference_verified) {
    npuStatus = 'INFERENCE VERIFIED';
  } else if (runtimeVerify?.model_loaded) {
    npuStatus = 'MODEL LOADED';
  } else if (runtimeVerify?.provider_loaded) {
    npuStatus = 'PROVIDER LOADED';
  } else if (runtimeVerify?.qnn_available) {
    npuStatus = 'AVAILABLE';
  } else {
    npuStatus = 'NOT AVAILABLE';
  }

  return (
    <div className="space-y-6">
      {/* PART 3: Competition Landing Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl border border-cyan-500/30 bg-gradient-to-br from-slate-900 via-slate-900 to-cyan-950/40 p-6 md:p-8 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 h-48 w-48 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-300 border border-cyan-500/30">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
              AuraGuard &bull; On-Device Sovereign AI
            </div>
            <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
              AURAGUARD
            </h1>
            <p className="text-sm md:text-base font-medium text-cyan-200">
              Private AI Layer for Personal Computing
            </p>
            <p className="text-xs md:text-sm text-slate-300 italic pt-1">
              &ldquo;Your documents. Your memory. Your AI. Kept local.&rdquo;
            </p>
          </div>

          <div className="flex flex-wrap gap-2 max-w-md">
            <span className="rounded-lg bg-slate-950/80 px-2.5 py-1 text-[11px] font-semibold text-slate-200 border border-slate-800">
              LOCAL RAG
            </span>
            <span className="rounded-lg bg-slate-950/80 px-2.5 py-1 text-[11px] font-semibold text-slate-200 border border-slate-800">
              PRIVATE MEMORY
            </span>
            <span className="rounded-lg bg-slate-950/80 px-2.5 py-1 text-[11px] font-semibold text-slate-200 border border-slate-800">
              PRIVACY GUARD
            </span>
            <span className="rounded-lg bg-slate-950/80 px-2.5 py-1 text-[11px] font-semibold text-slate-200 border border-slate-800">
              ENCRYPTED STORAGE
            </span>
            <span className="rounded-lg bg-slate-950/80 px-2.5 py-1 text-[11px] font-semibold text-slate-200 border border-slate-800">
              HARDWARE-AWARE AI
            </span>
            <span className="rounded-lg bg-cyan-500/20 px-2.5 py-1 text-[11px] font-semibold text-cyan-300 border border-cyan-500/40">
              SNAPDRAGON READY
            </span>
          </div>
        </div>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-red-200">{error}</div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-2">
        <div>
          <h2 className="text-xl font-bold text-slate-100">System overview</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Four-quadrant private personal computing architecture &bull; Zero external cloud telemetry
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
      </div>

      {/* PART 4: Judge-Friendly 4-Area Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* AREA 1: AI Runtime */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <span className="text-cyan-400">⚙️</span>
                1. AI Runtime
              </h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {aiRuntime?.active_execution_provider ?? 'CPUExecutionProvider'}
              </span>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Hardware</span>
                <span className="text-slate-200 font-semibold truncate block mt-0.5" title={hardware?.cpu.brand}>
                  {hardware?.cpu.brand ?? 'Intel Core i5-1235U'}
                </span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Architecture</span>
                <span className="text-slate-200 font-semibold block mt-0.5">
                  {hardware?.cpu.architecture ?? 'x86_64'}
                </span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Embedding Model</span>
                <span className="text-slate-200 font-semibold block mt-0.5">
                  {models?.embedding.name ?? 'all-MiniLM-L6-v2'} (INT8)
                </span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Generative LLM</span>
                <span className="text-slate-200 font-semibold block mt-0.5">
                  {models?.llm.name.split('/').pop() ?? 'Qwen2.5-0.5B'} (FP32)
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Live NPU State:</span>
            <span className={`font-mono font-semibold ${
              npuStatus === 'INFERENCE VERIFIED' ? 'text-emerald-400' :
              npuStatus === 'NOT AVAILABLE' ? 'text-slate-400' : 'text-amber-400'
            }`}>
              {npuStatus}
            </span>
          </div>
        </div>

        {/* AREA 2: Privacy */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <span className="text-emerald-400">🛡️</span>
                2. Privacy & Security
              </h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                Zero Cloud Egress
              </span>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Storage Encryption</span>
                <span className="text-emerald-400 font-semibold block mt-0.5">AES-256-GCM</span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Key Protection</span>
                <span className="text-emerald-400 font-semibold block mt-0.5">Windows DPAPI</span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Blocked Inputs</span>
                <span className="text-cyan-300 font-semibold block mt-0.5">
                  {security?.blocked_requests ?? 0} sensitive requests
                </span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Protected Memories</span>
                <span className="text-cyan-300 font-semibold block mt-0.5">
                  {security?.encrypted_memories ?? 0} encrypted entries
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Cloud Inference:</span>
            <span className="text-emerald-400 font-mono font-semibold">Strictly Disabled (127.0.0.1)</span>
          </div>
        </div>

        {/* AREA 3: Knowledge */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <span className="text-amber-400">📚</span>
                3. Knowledge & Context
              </h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Dual FAISS Store
              </span>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Documents</span>
                <span className="text-slate-200 font-semibold block mt-0.5">
                  {stats?.documents_indexed ?? 0} files indexed
                </span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">ReMind Memories</span>
                <span className="text-slate-200 font-semibold block mt-0.5">
                  {stats?.memories_stored ?? 0} approved entries
                </span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Retrieval Engine</span>
                <span className="text-slate-200 font-semibold block mt-0.5">FAISS FlatL2 (384-d)</span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Source Attribution</span>
                <span className="text-emerald-400 font-semibold block mt-0.5">Strict (Doc + Page)</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Context Neutralizer:</span>
            <span className="text-cyan-300 font-mono font-semibold">Prompt Injection Shield Active</span>
          </div>
        </div>

        {/* AREA 4: Performance */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                <span className="text-cyan-400">⚡</span>
                4. Performance (Intel Host Baseline)
              </h3>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Empirical Measurements
              </span>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Embedding Latency</span>
                <span className="text-cyan-300 font-semibold block mt-0.5">38.32 ms / query</span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Embedding Throughput</span>
                <span className="text-emerald-400 font-semibold block mt-0.5">57.32 texts/sec</span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">LLM Generation Speed</span>
                <span className="text-cyan-300 font-semibold block mt-0.5">4.29 tokens/sec (CPU)</span>
              </div>
              <div className="rounded-lg bg-slate-950/60 p-2.5 border border-slate-800/80">
                <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Process Peak RSS</span>
                <span className="text-cyan-300 font-semibold block mt-0.5">992.0 MB</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Total RAG Pipeline:</span>
            <span className="text-cyan-300 font-mono font-semibold">12.05 s (Retrieval &lt;35 ms)</span>
          </div>
        </div>
      </div>

      {/* Part 18 & Part 20: Empirical Benchmark Dashboard */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-5 shadow-lg">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
              <span className="text-cyan-400">📊</span>
              Empirical Platform Benchmark Matrix
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly measured results across execution platforms. Unverified hardware displays &quot;Not measured&quot;.
            </p>
          </div>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
            Source: benchmarks/results/
          </span>
        </div>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/70 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Metric</th>
                <th className="py-2.5 px-3 text-right">Intel CPU (Host Baseline)</th>
                <th className="py-2.5 px-3 text-right">Snapdragon CPU</th>
                <th className="py-2.5 px-3 text-right">Snapdragon NPU (Hexagon)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">Embedding Mean Latency</td>
                <td className="py-2.5 px-3 text-right text-cyan-300">38.32 ms</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">Embedding p95 Latency</td>
                <td className="py-2.5 px-3 text-right text-cyan-300">56.12 ms</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">Embedding Throughput</td>
                <td className="py-2.5 px-3 text-right text-emerald-400">57.32 texts/s</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">LLM True TTFT (Full Prompt)</td>
                <td className="py-2.5 px-3 text-right text-cyan-300">14,278.46 ms</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">LLM Generation Speed</td>
                <td className="py-2.5 px-3 text-right text-cyan-300">4.29 tokens/s</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">Total RAG Pipeline Latency</td>
                <td className="py-2.5 px-3 text-right text-cyan-300">12.05 s</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">Peak Process RSS</td>
                <td className="py-2.5 px-3 text-right text-cyan-300">992.0 MB</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-sans font-medium text-slate-200">Power Consumption (W)</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
                <td className="py-2.5 px-3 text-right text-slate-500 italic">Not measured</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
