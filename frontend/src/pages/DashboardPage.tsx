import React from 'react';
import { useAuthStore } from '../stores/authStore';
import { Cpu, Users, Layers, ShieldCheck } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuthStore();

  const stats = [
    { name: 'Licenças Ativas', value: '45', icon: Layers, color: 'text-emerald-400' },
    { name: 'Ativos Gerenciados', value: '184', icon: Cpu, color: 'text-blue-400' },
    { name: 'Colaboradores', value: '32', icon: Users, color: 'text-amber-400' },
    { name: 'SLA Geral', value: '98.4%', icon: ShieldCheck, color: 'text-brand-primary' },
  ];

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">
          Dashboard
        </h1>
        <p className="text-brand-muted text-sm mt-1">
          Bem-vindo de volta, <span className="text-white font-medium">{user?.nome}</span>.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.name} className="border border-brand-border bg-brand-card p-6 flex items-center justify-between">
            <div>
              <span className="text-xs font-mono uppercase tracking-wider text-brand-muted">
                {stat.name}
              </span>
              <h3 className="text-3xl font-bold font-mono text-brand-text mt-2">
                {stat.value}
              </h3>
            </div>
            <stat.icon size={28} className={stat.color} />
          </div>
        ))}
      </div>

      {/* Legacy Migration Notice */}
      <div className="border border-brand-primary/20 bg-brand-primary/5 p-6 font-mono text-sm space-y-3">
        <h4 className="text-brand-primary font-bold uppercase tracking-wider">
          Status de Migração do Sistema (Python FastAPI ➜ Go REST)
        </h4>
        <p className="text-brand-muted">
          Estamos migrando a infraestrutura do AssetTrack TI. A Fase 1 (Autenticação, Sessões JWT, CRUD de Usuários e sistema QR/PIN) foi concluída com sucesso na stack Go (Gin + GORM).
        </p>
        <div className="flex items-center space-x-4 text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="h-2.5 w-2.5 bg-brand-primary" />
            <span className="text-brand-text">Fase 1 (Pronto)</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="h-2.5 w-2.5 bg-brand-border" />
            <span className="text-brand-muted/70">Fase 2-4 (Em planejamento)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
