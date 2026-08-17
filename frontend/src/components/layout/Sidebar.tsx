import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { apiClient as api } from '../../api/client';
import {
  LayoutDashboard,
  Users,
  QrCode,
  LogOut,
  Briefcase,
  Cpu,
  FileSpreadsheet,
  Wrench,
  ArrowLeftRight,
  MessageSquare,
  Truck,
  ClipboardList,
  Columns3,
  BellRing,
  FileSignature,
  Webhook,
  Database
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuthStore();

  const menuItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Ativos & Inventário', path: '/assets', icon: Cpu },
    { name: 'Central de Suporte', path: '/servicos', icon: MessageSquare },
    { name: 'Manutenções', path: '/manutencoes', icon: Wrench },
    { name: 'Prev. Programada', path: '/manutencao-preventiva', icon: ClipboardList },
    { name: 'Kanban', path: '/kanban', icon: Columns3 },
    { name: 'Alertas', path: '/alertas', icon: BellRing },
    { name: 'Empréstimos', path: '/emprestimos', icon: ArrowLeftRight },
    { name: 'Fornecedores', path: '/fornecedores', icon: Truck, roleLimit: ['admin', 'gerente_ti', 'gerente_infra', 'comprador'] },
    { name: 'Compras', path: '/compras', icon: Briefcase, roleLimit: ['admin', 'gerente_ti', 'gerente_infra', 'comprador'] },
    { name: 'Portal RH', path: '/rh', icon: FileSignature, roleLimit: ['admin', 'rh', 'gerente_ti', 'gerente_infra'] },
    { name: 'Usuários', path: '/users', icon: Users, roleLimit: ['admin', 'gerente_ti'] },
    { name: 'Webhooks', path: '/webhooks', icon: Webhook, roleLimit: ['admin'] },
    { name: 'Backup & Restore', path: '/backups', icon: Database, roleLimit: ['admin'] },
    { name: 'Meu Crachá QR', path: '/badge', icon: QrCode },
  ];

  const adminModules = [
    { name: 'Relatórios (Fase 4)', path: '#', icon: FileSpreadsheet, disabled: true },
  ];

  return (
    <aside className="w-64 bg-brand-dark border-r border-brand-border h-screen flex flex-col justify-between select-none">
      <div className="flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-6 border-b border-brand-border">
          <span className="font-bold text-brand-primary tracking-wider text-xl uppercase font-mono">
            AssetTrack<span className="text-white font-sans font-light lowercase">.ti</span>
          </span>
        </div>

        {/* User Info Card */}
        <NavLink to="/profile" className="p-4 border-b border-brand-border bg-brand-card/30 hover:bg-brand-card/70 transition-colors block cursor-pointer">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 border border-brand-primary flex items-center justify-center font-mono text-brand-primary text-lg bg-brand-primary/5 overflow-hidden">
              {user?.avatar_url ? (
                <img src={`${api.defaults.baseURL}${user.avatar_url}`} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                user?.nome.substring(0, 2).toUpperCase()
              )}
            </div>
            <div className="overflow-hidden">
              <h4 className="text-sm font-semibold truncate text-brand-text group-hover:text-brand-primary">{user?.nome}</h4>
              <span className="text-xs text-brand-primary font-mono uppercase bg-brand-primary/10 px-1.5 py-0.5 border border-brand-primary/20 mt-1 inline-block">
                {user?.role.replace('_', ' ')}
              </span>
            </div>
          </div>
        </NavLink>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {menuItems.map((item) => {
            if (item.roleLimit && !item.roleLimit.includes(user?.role || '')) {
              return null;
            }
            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-4 py-3 border text-sm transition-all duration-150 ${
                    isActive
                      ? 'border-brand-primary bg-brand-primary/5 text-brand-primary font-medium font-mono'
                      : 'border-transparent text-brand-muted hover:text-brand-text hover:bg-brand-card/50'
                  }`
                }
              >
                <item.icon size={18} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}

          <div className="pt-4 pb-2 px-4 text-xs font-mono font-semibold text-brand-muted/70 tracking-widest uppercase">
            Módulos Legados
          </div>

          {adminModules.map((item) => (
            <div
              key={item.name}
              className="flex items-center space-x-3 px-4 py-3 text-sm text-brand-muted/40 cursor-not-allowed"
            >
              <item.icon size={18} />
              <span>{item.name}</span>
            </div>
          ))}
        </nav>
      </div>

      {/* Logout */}
      <div className="p-4 border-t border-brand-border">
        <button
          onClick={logout}
          className="w-full flex items-center space-x-3 px-4 py-3 border border-red-500/20 text-red-400 hover:bg-red-500/10 text-sm font-mono transition-all duration-150"
        >
          <LogOut size={18} />
          <span>Encerrar Sessão</span>
        </button>
      </div>
    </aside>
  );
};
