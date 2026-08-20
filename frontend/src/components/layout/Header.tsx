import React from 'react';
import { useAuthStore } from '../../stores/authStore';
import { Link } from 'react-router-dom';
import { Bell, CircleHelp, Home, Plus, Search, Settings, ShieldCheck, ShieldAlert, User as UserIcon } from 'lucide-react';
import { triggerEmergencyAlertModal } from '../emergency/EmergencyGlobalHandler';

export const Header: React.FC = () => {
  const { user } = useAuthStore();
  const canAccessSettings = ['admin', 'gerente_ti', 'gerente_infra'].includes(user?.role?.toLowerCase() || '');

  return (
    <header className="h-14 shrink-0 border-b border-white/20 flex items-center justify-between px-3 md:px-5 bg-[#345b7d]/78 text-white backdrop-blur-md sticky top-0 z-50 shadow-[0_2px_12px_rgba(9,30,66,.16)]">
      <div className="flex min-w-0 items-center gap-2">
        <Link to="/" className="grid h-8 w-8 place-items-center rounded bg-white/16 hover:bg-white/28" title="Início" aria-label="Início">
          <Home size={17} />
        </Link>
        <Link to="/kanban" className="hidden sm:inline-flex h-8 items-center gap-2 rounded bg-white/16 px-3 text-sm font-semibold hover:bg-white/28">
          <span className="text-base leading-none">▥</span> Projetos
        </Link>
        <label className="hidden md:flex h-8 w-52 lg:w-64 items-center gap-2 rounded bg-white/16 px-3 text-white/85 focus-within:bg-white/24" title="Busca global">
          <Search size={15} />
          <input className="w-full bg-transparent text-sm outline-none placeholder:text-white/65" placeholder="Buscar no AssetTrack" aria-label="Busca global" />
        </label>
      </div>

      <div className="flex items-center gap-1.5">
        {/* Emergency Trigger Button for ALL users */}
        <button
          onClick={triggerEmergencyAlertModal}
          className="hidden xl:flex bg-red-600/85 hover:bg-red-600 text-white font-bold text-xs px-3 py-1.5 rounded border border-red-300/30 items-center space-x-1.5 transition-all shadow-sm"
          title="Disparar um alerta emergencial para a equipe de TI"
        >
          <ShieldAlert size={15} />
          <span>Alerta Emergencial</span>
        </button>

        {user?.role === 'admin' && (
          <div className="hidden lg:flex items-center space-x-1 text-white border border-white/25 px-2 py-1 bg-white/10 rounded text-xs">
            <ShieldCheck size={14} />
            <span>ROOT</span>
          </div>
        )}
        <Link to="/kanban" className="grid h-8 w-8 place-items-center rounded bg-white/16 hover:bg-white/28" title="Criar ou abrir projetos" aria-label="Projetos">
          <Plus size={18} />
        </Link>
        <Link to="/alertas" className="grid h-8 w-8 place-items-center rounded bg-white/16 hover:bg-white/28" title="Notificações" aria-label="Notificações">
          <Bell size={16} />
        </Link>
        <button className="hidden sm:grid h-8 w-8 place-items-center rounded bg-white/16 hover:bg-white/28" title="Ajuda" aria-label="Ajuda"><CircleHelp size={16} /></button>
        {canAccessSettings && (
          <Link to="/configuracoes" className="hidden sm:grid h-8 w-8 place-items-center rounded bg-white/16 hover:bg-white/28" title="Configurações" aria-label="Configurações"><Settings size={16} /></Link>
        )}
        <Link to="/profile" className="flex items-center gap-2 rounded bg-white/10 py-1 pl-1 pr-2 text-sm hover:bg-white/20">
          <span className="grid h-7 w-7 place-items-center rounded-full bg-[#0c66e4] text-xs font-bold"><UserIcon size={15} /></span>
          <span className="hidden font-medium md:block max-w-28 truncate">{user?.nome}</span>
        </Link>
      </div>
    </header>
  );
};
