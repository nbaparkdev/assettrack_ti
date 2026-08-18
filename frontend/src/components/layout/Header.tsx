import React from 'react';
import { useAuthStore } from '../../stores/authStore';
import { ShieldCheck, User as UserIcon, ShieldAlert } from 'lucide-react';
import { triggerEmergencyAlertModal } from '../emergency/EmergencyGlobalHandler';

export const Header: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <header className="h-16 border-b border-brand-border flex items-center justify-between px-8 bg-brand-dark/50 backdrop-blur-md sticky top-0 z-50">
      <div className="flex items-center space-x-2">
        <span className="h-2 w-2 bg-brand-primary animate-pulse" />
        <span className="text-xs font-mono text-brand-muted uppercase tracking-wider">
          AssetTrack TI - v2.0
        </span>
      </div>

      <div className="flex items-center space-x-4">
        {/* Emergency Trigger Button for ALL users */}
        <button
          onClick={triggerEmergencyAlertModal}
          className="bg-red-600/20 hover:bg-red-600 text-red-400 hover:text-white font-mono font-bold text-xs uppercase px-3 py-1.5 border border-red-500/40 hover:border-red-600 flex items-center space-x-1.5 transition-all shadow-sm shadow-red-500/20 animate-pulse"
          title="Disparar um alerta emergencial para a equipe de TI"
        >
          <ShieldAlert size={15} />
          <span>Alerta Emergencial</span>
        </button>

        {user?.role === 'admin' && (
          <div className="flex items-center space-x-1 text-brand-primary border border-brand-primary/30 px-2 py-1 bg-brand-primary/5 text-xs font-mono">
            <ShieldCheck size={14} />
            <span>ROOT</span>
          </div>
        )}
        <div className="flex items-center space-x-2 text-brand-text text-sm">
          <UserIcon size={16} className="text-brand-primary" />
          <span className="font-medium">{user?.nome}</span>
        </div>
      </div>
    </header>
  );
};
