import { Route, Routes, NavLink } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import DocumentsPage from './pages/DocumentsPage';
import AskPage from './pages/AskPage';

const navItems = [
  { label: 'Dashboard', to: '/' },
  { label: 'Documents', to: '/documents' },
  { label: 'Ask AuraGuard', to: '/ask' },
  { label: 'Memory', to: '/memory' },
  { label: 'Privacy', to: '/privacy' },
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
          <Route path="/memory" element={<div className="rounded-xl border border-slate-800 bg-slate-900 p-6">Memory view coming soon.</div>} />
          <Route path="/privacy" element={<div className="rounded-xl border border-slate-800 bg-slate-900 p-6">Privacy view coming soon.</div>} />
          <Route path="/settings" element={<div className="rounded-xl border border-slate-800 bg-slate-900 p-6">Settings view coming soon.</div>} />
        </Routes>
      </main>
    </div>
  );
}
