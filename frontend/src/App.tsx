import { Route, Routes, NavLink } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import AskPage from './pages/AskPage';
import MemoryPage from './pages/MemoryPage';
import PrivacyCenterPage from './pages/PrivacyCenterPage';

const navItems = [
  { label: 'Dashboard', to: '/', icon: '⊞', desc: 'System overview' },
  { label: 'Documents', to: '/documents', icon: '📄', desc: 'PDF ingestion & RAG' },
  { label: 'Ask AuraGuard', to: '/ask', icon: '💬', desc: 'Local context intelligence' },
  { label: 'Memory (ReMind)', to: '/memory', icon: '🧠', desc: 'Private memory store' },
  { label: 'Privacy Center', to: '/privacy', icon: '🛡️', desc: 'Policy & event ledger' },
  { label: 'Settings', to: '/settings', icon: '⚙️', desc: 'Runtime configuration' },
];

function SettingsPage() {
  return (
    <div className="space-y-6">
      <header>
        <p className="text-sm uppercase tracking-[0.2em] text-cyan-400">Settings</p>
        <h2 className="mt-1 text-3xl font-bold">Runtime Configuration</h2>
        <p className="text-xs text-slate-400 mt-1">
          AuraGuard operates 100% locally. All configuration is persisted on-device only.
        </p>
      </header>

      {/* Current Runtime */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 space-y-4">
        <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3 flex items-center gap-2">
          <span className="text-cyan-400">⚙️</span> Current Runtime
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 text-xs font-mono">
          <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
            <p className="text-slate-400 uppercase text-[10px]">Local LLM</p>
            <p className="text-slate-100 font-semibold mt-1">Qwen2.5-0.5B-Instruct</p>
            <p className="text-slate-500 text-[11px] mt-0.5">FP32 · On-device inference · Zero cloud</p>
          </div>
          <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
            <p className="text-slate-400 uppercase text-[10px]">Embedding Model</p>
            <p className="text-slate-100 font-semibold mt-1">all-MiniLM-L6-v2</p>
            <p className="text-slate-500 text-[11px] mt-0.5">INT8 ONNX · 384-dim · FAISS FlatL2</p>
          </div>
          <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
            <p className="text-slate-400 uppercase text-[10px]">Active Execution Provider</p>
            <p className="text-cyan-300 font-semibold mt-1">CPUExecutionProvider</p>
            <p className="text-slate-500 text-[11px] mt-0.5">Auto-detected Intel x86_64 host</p>
          </div>
          <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
            <p className="text-slate-400 uppercase text-[10px]">Vector Index</p>
            <p className="text-slate-100 font-semibold mt-1">FAISS IndexFlatL2</p>
            <p className="text-slate-500 text-[11px] mt-0.5">Partitioned: documents / memories</p>
          </div>
        </div>
      </div>

      {/* Storage & Security */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 space-y-4">
        <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3 flex items-center gap-2">
          <span className="text-emerald-400">🔒</span> Storage & Security
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 text-xs font-mono">
          <div className="rounded-lg bg-slate-950/70 p-3 border border-emerald-500/20">
            <p className="text-slate-400 uppercase text-[10px]">Storage Encryption</p>
            <p className="text-emerald-400 font-bold mt-1">AES-256-GCM</p>
            <p className="text-slate-500 text-[11px] mt-0.5">96-bit IV · 128-bit auth tag · GMAC verified</p>
          </div>
          <div className="rounded-lg bg-slate-950/70 p-3 border border-emerald-500/20">
            <p className="text-slate-400 uppercase text-[10px]">Key Protection</p>
            <p className="text-emerald-400 font-bold mt-1">Windows DPAPI</p>
            <p className="text-slate-500 text-[11px] mt-0.5">Bound to authenticated user session · CryptProtectData</p>
          </div>
          <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
            <p className="text-slate-400 uppercase text-[10px]">Network Policy</p>
            <p className="text-red-400 font-bold mt-1">STRICTLY LOCAL</p>
            <p className="text-slate-500 text-[11px] mt-0.5">All inference bound to 127.0.0.1 · Zero egress</p>
          </div>
          <div className="rounded-lg bg-slate-950/70 p-3 border border-slate-800">
            <p className="text-slate-400 uppercase text-[10px]">Plaintext Storage</p>
            <p className="text-emerald-400 font-bold mt-1">ZERO</p>
            <p className="text-slate-500 text-[11px] mt-0.5">Keys never in .env · Never in logs · Never in API</p>
          </div>
        </div>
      </div>

      {/* Snapdragon Target */}
      <div className="rounded-xl border border-cyan-500/30 bg-gradient-to-br from-slate-900 to-cyan-950/20 p-6 space-y-3">
        <h3 className="text-base font-semibold text-slate-100 border-b border-slate-800 pb-3 flex items-center gap-2">
          <span className="text-cyan-400">🎯</span> Snapdragon Target Architecture
        </h3>
        <div className="rounded-lg bg-slate-950/80 p-4 border border-slate-800 text-xs space-y-2">
          <p className="text-slate-300"><strong className="text-cyan-300">Target:</strong> Qualcomm Snapdragon X Elite / Plus (Oryon CPU + 45 TOPS Hexagon NPU)</p>
          <p className="text-slate-300"><strong className="text-cyan-300">Provider:</strong> QNNExecutionProvider (auto-activated on Snapdragon detection)</p>
          <p className="text-slate-300"><strong className="text-cyan-300">Models:</strong> INT8 quantized ONNX embeddings prepared · INT4 LLM quantization planned</p>
          <p className="text-amber-300 font-mono text-[11px] mt-2">
            ⚠ NPU execution NOT measured on current Intel development machine. All Snapdragon performance figures are TARGET values pending physical hardware validation.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 w-64 border-r border-slate-800 bg-slate-900/95 backdrop-blur-sm flex flex-col">
        {/* Brand */}
        <div className="p-5 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 text-sm font-bold">
              AG
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">AuraGuard</h1>
              <p className="text-[10px] text-slate-500 leading-tight">Private AI Layer</p>
            </div>
          </div>
          {/* System status pill */}
          <div className="mt-3 flex items-center gap-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse flex-shrink-0" />
            <span className="text-[10px] font-mono text-emerald-300">LOCAL ONLY · 127.0.0.1</span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-300 ring-1 ring-cyan-500/30'
                    : 'text-slate-400 hover:bg-slate-800/70 hover:text-slate-100'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <span className="text-base flex-shrink-0">{item.icon}</span>
                  <div className="min-w-0">
                    <p className={`leading-tight ${isActive ? 'text-cyan-300' : ''}`}>{item.label}</p>
                    <p className="text-[10px] text-slate-500 leading-tight truncate">{item.desc}</p>
                  </div>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 space-y-2">
          <div className="rounded-md bg-slate-950/60 border border-slate-800 p-2.5 text-[10px] font-mono text-slate-500 space-y-1">
            <div className="flex justify-between">
              <span>Snapdragon NPU</span>
              <span className="text-slate-600">NOT DETECTED</span>
            </div>
            <div className="flex justify-between">
              <span>Runtime</span>
              <span className="text-cyan-400/70">CPU</span>
            </div>
            <div className="flex justify-between">
              <span>Encryption</span>
              <span className="text-emerald-400/70">AES-256</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="ml-64 min-h-screen">
        <div className="max-w-7xl mx-auto p-6 md:p-8">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/ask" element={<AskPage />} />
            <Route path="/memory" element={<MemoryPage />} />
            <Route path="/privacy" element={<PrivacyCenterPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
