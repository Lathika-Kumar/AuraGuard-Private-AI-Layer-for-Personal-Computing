import { Route, Routes, NavLink } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import AskPage from './pages/AskPage';
import MemoryPage from './pages/MemoryPage';
import PrivacyCenterPage from './pages/PrivacyCenterPage';

const navItems = [
  { label: 'Dashboard', to: '/' },
  { label: 'Documents', to: '/documents' },
  { label: 'Ask AuraGuard', to: '/ask' },
  { label: 'Memory (ReMind)', to: '/memory' },
  { label: 'Privacy Center', to: '/privacy' },
  { label: 'Settings', to: '/settings' },
];

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <aside className="fixed inset-y-0 left-0 w-64 border-r border-slate-800 bg-slate-900/90 p-5 backdrop-blur">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-cyan-400">AuraGuard</h1>
          <p className="mt-1 text-sm text-slate-400">Local-first AI layer</p>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition ${
                  isActive
                    ? 'bg-cyan-500/20 text-cyan-300 ring-1 ring-cyan-500/40'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="ml-64 min-h-screen p-8">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/ask" element={<AskPage />} />
          <Route path="/memory" element={<MemoryPage />} />
          <Route path="/privacy" element={<PrivacyCenterPage />} />
          <Route
            path="/settings"
            element={
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-6 space-y-4">
                <h3 className="text-xl font-bold text-slate-100">Local Settings</h3>
                <p className="text-sm text-slate-400">
                  AuraGuard runs 100% locally on your personal computing environment. No telemetry or private context is sent over external networks.
                </p>
                <div className="mt-4 rounded-lg bg-slate-950/70 p-4 border border-slate-800 text-xs text-slate-400 space-y-2">
                  <p><strong className="text-slate-300">Target Architecture:</strong> Qualcomm Snapdragon X Elite (Hexagon NPU)</p>
                  <p><strong className="text-slate-300">Local LLM:</strong> Qwen2.5-0.5B-Instruct</p>
                  <p><strong className="text-slate-300">Local Embeddings:</strong> sentence-transformers/all-MiniLM-L6-v2</p>
                  <p><strong className="text-slate-300">Vector Index:</strong> FAISS (Partitioned namespaces: documents / memories)</p>
                </div>
              </div>
            }
          />
        </Routes>
      </main>
    </div>
  );
}
