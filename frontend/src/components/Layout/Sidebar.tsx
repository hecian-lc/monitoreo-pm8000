import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  Table2,
  FolderOpen,
  FileText,
  Settings,
  Zap,
} from 'lucide-react';

const links = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/trends', icon: TrendingUp, label: 'Tendencias' },
  { to: '/data', icon: Table2, label: 'Datos' },
  { to: '/measurements', icon: FolderOpen, label: 'Mediciones' },
  { to: '/reports', icon: FileText, label: 'Informes' },
  { to: '/settings', icon: Settings, label: 'Configuraci\u00f3n' },
];

export default function Sidebar() {
  return (
    <aside className="w-56 bg-slate-900 text-white flex flex-col min-h-screen">
      <div className="p-4 flex items-center gap-2 border-b border-slate-700">
        <Zap className="w-6 h-6 text-yellow-400" />
        <span className="font-bold text-sm">Monitoreo PM8000</span>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-slate-700 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 text-xs text-slate-500 border-t border-slate-700">
        v0.1.0
      </div>
    </aside>
  );
}
