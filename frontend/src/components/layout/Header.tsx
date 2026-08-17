import React from 'react';
import { useAuthStore } from '../../stores/authStore';
import { ShieldCheck, User as UserIcon } from 'lucide-react';

export const Header: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <header className="h-16 border-b border-brand-border flex items-center justify-between px-8 bg-brand-dark/50 backdrop-blur-md sticky top-0 z-50">
      <div className="flex items-center space-x-2">
        <span className="h-2 w-2 bg-brand-primary animate-pulse" />
        <span className="text-xs font-mono text-brand-muted uppercase tracking-wider">
          Fase 1: Ambiente de Homologação Ativo
        </span>
      </div>

      <div className="flex items-center space-x-4">
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
