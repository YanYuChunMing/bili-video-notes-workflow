import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, ListTodo, Settings, ChevronLeft, ChevronRight, Menu, X } from 'lucide-react';

const navItems = [
  { to: '/', label: '仪表盘', icon: LayoutDashboard },
  { to: '/tasks', label: '任务', icon: ListTodo },
  { to: '/settings', label: '设置', icon: Settings },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-white text-sm font-bold">B</span>
            </div>
            <span className="font-semibold text-text text-sm">B站笔记</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="hidden lg:block p-1 rounded hover:bg-gray-100 text-text-secondary"
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </button>
        <button onClick={() => setMobileOpen(false)} className="lg:hidden p-1 rounded hover:bg-gray-100">
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => {
          const isActive = to === '/' ? location.pathname === '/' : location.pathname.startsWith(to);
          return (
            <NavLink
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-text-secondary hover:bg-gray-100 hover:text-text'
              } ${collapsed ? 'justify-center lg:px-2' : ''}`}
            >
              <Icon size={20} />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          );
        })}
      </nav>

      <div className="p-4 border-t border-gray-100 hidden lg:block">
        {!collapsed && <p className="text-xs text-text-secondary">bili-video-notes v1.2</p>}
      </div>
    </div>
  );

  return (
    <>
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-40 p-2 rounded-lg bg-white shadow-md text-text-secondary"
      >
        <Menu size={20} />
      </button>

      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-30 bg-black/30" onClick={() => setMobileOpen(false)} />
      )}

      <aside
        className={`fixed lg:static left-0 top-0 h-full z-40 bg-white border-r border-gray-100 transition-all duration-200 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } ${collapsed ? 'w-16' : 'w-60'}`}
      >
        {sidebarContent}
      </aside>
    </>
  );
}
