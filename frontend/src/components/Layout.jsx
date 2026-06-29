import { Link, Outlet, useLocation } from 'react-router-dom';
import { Activity, Shield, LayoutGrid, BarChart3 } from 'lucide-react';

export default function Layout() {
  const location = useLocation();
  
  const navItems = [
    { name: 'Log Input', path: '/', icon: Activity },
    { name: 'Pipeline View', path: '/pipeline', icon: Shield },
    { name: 'ATT&CK Heatmap', path: '/heatmap', icon: LayoutGrid },
    { name: 'Metrics', path: '/metrics', icon: BarChart3 },
  ];

  return (
    <div className="flex h-screen bg-slate-900 text-slate-50 overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl flex flex-col">
        <div className="p-6 border-b border-slate-800">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-400" />
            HuntGPT-Shield
          </h1>
        </div>
        
        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  isActive 
                    ? 'bg-blue-600/10 text-blue-400' 
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
              >
                <Icon className={`h-5 w-5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-900 to-slate-950">
        <div className="p-8 max-w-7xl mx-auto h-full">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
