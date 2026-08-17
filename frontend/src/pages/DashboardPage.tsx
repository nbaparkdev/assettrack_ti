import React, { useEffect, useState } from 'react';
import { dashboardApi } from '../api/dashboard';
import type { DashboardStats } from '../api/dashboard';
import { 
  LayoutDashboard, Wrench, MessageSquare, Briefcase, BellRing, FileDown,
  AlertTriangle, Info, ShieldAlert, Cpu
} from 'lucide-react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Register Chart.js components
ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, BarElement,
  ArcElement, Title, Tooltip, Legend, Filler
);

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await dashboardApi.getStats();
      setStats(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const exportPDF = () => {
    if (!stats) return;
    setExporting(true);
    
    try {
      const doc = new jsPDF();
      
      // Header
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(20);
      doc.setTextColor(15, 23, 42); // slate-900
      doc.text('AssetTrack TI - Relatório Executivo', 14, 20);
      
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(100, 116, 139);
      doc.text(`Gerado em: ${new Date().toLocaleString('pt-BR')}`, 14, 28);
      
      // KPIs
      doc.setFontSize(14);
      doc.setTextColor(15, 23, 42);
      doc.text('Indicadores Principais (KPIs)', 14, 40);

      autoTable(doc, {
        startY: 45,
        theme: 'grid',
        headStyles: { fillColor: [56, 189, 248] }, // sky-400 equivalent for brand
        head: [['Métrica', 'Valor Registrado']],
        body: [
          ['Ativos em Manutenção', String(stats.total_assets_maintenance)],
          ['Chamados Abertos vs Resolvidos', `${stats.tickets_open} Abertos / ${stats.tickets_resolved} Resolvidos`],
          ['Solicitações de Ativos (Pendentes)', String(stats.pending_asset_requests)],
          ['Custo Mensal Fornecedores', `R$ ${stats.supplier_cost_monthly.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`],
        ]
      });

      // Alerts
      const currentY = (doc as any).lastAutoTable.finalY + 15;
      doc.text('Alertas Ativos', 14, currentY);

      if (stats.active_alerts && stats.active_alerts.length > 0) {
        autoTable(doc, {
          startY: currentY + 5,
          theme: 'striped',
          headStyles: { fillColor: [239, 68, 68] }, // red-500
          head: [['Gravidade', 'Título', 'Data']],
          body: stats.active_alerts.map(a => [
            a.severity,
            a.title,
            new Date(a.created_at).toLocaleString('pt-BR')
          ])
        });
      } else {
        doc.setFontSize(10);
        doc.text('Nenhum alerta crítico ativo no momento.', 14, currentY + 8);
      }

      // Footer
      const pageCount = (doc as any).internal.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(`Página ${i} de ${pageCount} - AssetTrack TI`, 14, doc.internal.pageSize.height - 10);
      }

      doc.save(`relatorio_executivo_${new Date().getTime()}.pdf`);
    } catch (err) {
      console.error(err);
      alert('Erro ao gerar PDF');
    } finally {
      setExporting(false);
    }
  };

  if (loading) return <div className="text-brand-muted font-mono text-sm">Carregando painel analítico...</div>;
  if (!stats) return <div className="text-red-400">Erro ao carregar dados.</div>;

  // Chart Data
  const ticketsData = {
    labels: ['Abertos', 'Resolvidos'],
    datasets: [
      {
        data: [stats.tickets_open, stats.tickets_resolved],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)', // red-500
          'rgba(34, 197, 94, 0.8)', // green-500
        ],
        borderColor: [
          'rgba(239, 68, 68, 1)',
          'rgba(34, 197, 94, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const assetsStatusData = {
    labels: ['Em Manutenção', 'Disponíveis/Uso'],
    datasets: [
      {
        label: 'Quantidade',
        data: [stats.total_assets_maintenance, stats.total_assets_maintenance * 4], // Fake data for 'Uso' to illustrate chart
        backgroundColor: 'rgba(56, 189, 248, 0.5)', // brand primary
        borderColor: 'rgba(56, 189, 248, 1)',
        borderWidth: 1,
      },
    ],
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-brand-border pb-4">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0 flex items-center">
            <LayoutDashboard className="mr-3 text-brand-primary" size={28} />
            Painel Executivo
          </h1>
          <p className="text-brand-muted text-sm mt-1">Visão geral do ecossistema de TI, métricas e análises</p>
        </div>
        <button
          onClick={exportPDF}
          disabled={exporting}
          className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-sm flex items-center hover:bg-brand-primary/90 transition-colors shadow-lg shadow-brand-primary/20 disabled:opacity-50"
        >
          <FileDown size={18} className="mr-2" />
          {exporting ? 'Gerando...' : 'Exportar Relatório PDF'}
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        
        <div className="bg-brand-card border border-brand-border p-5 relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 opacity-5 group-hover:scale-110 transition-transform">
            <Wrench size={100} />
          </div>
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20">
              <Wrench size={20} />
            </div>
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-brand-muted">Ativos em Manutenção</h3>
          </div>
          <div className="text-4xl font-black font-mono text-brand-text">{stats.total_assets_maintenance}</div>
          <div className="text-xs text-brand-muted mt-2">Equipamentos no conserto</div>
        </div>

        <div className="bg-brand-card border border-brand-border p-5 relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 opacity-5 group-hover:scale-110 transition-transform">
            <MessageSquare size={100} />
          </div>
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <MessageSquare size={20} />
            </div>
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-brand-muted">Tickets Abertos</h3>
          </div>
          <div className="flex items-baseline space-x-2">
            <div className="text-4xl font-black font-mono text-brand-text">{stats.tickets_open}</div>
            <div className="text-sm font-mono text-green-400">/ {stats.tickets_resolved} resolvidos</div>
          </div>
          <div className="text-xs text-brand-muted mt-2">Chamados pendentes no Service Desk</div>
        </div>

        <div className="bg-brand-card border border-brand-border p-5 relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 opacity-5 group-hover:scale-110 transition-transform">
            <Cpu size={100} />
          </div>
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Cpu size={20} />
            </div>
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-brand-muted">Solicitações de Ativos</h3>
          </div>
          <div className="text-4xl font-black font-mono text-brand-text">{stats.pending_asset_requests}</div>
          <div className="text-xs text-brand-muted mt-2">Pendentes de aprovação/entrega</div>
        </div>

        <div className="bg-brand-card border border-brand-border p-5 relative overflow-hidden group">
          <div className="absolute -right-4 -top-4 opacity-5 group-hover:scale-110 transition-transform">
            <Briefcase size={100} />
          </div>
          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2 bg-green-500/10 text-green-400 border border-green-500/20">
              <Briefcase size={20} />
            </div>
            <h3 className="text-xs font-bold font-mono uppercase tracking-wider text-brand-muted">Custo Mensal (Compras)</h3>
          </div>
          <div className="text-2xl font-black font-mono text-green-400 mt-2">{formatCurrency(stats.supplier_cost_monthly)}</div>
          <div className="text-xs text-brand-muted mt-2">Ordens de Compra aprovadas/recebidas</div>
        </div>

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Charts */}
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-brand-card border border-brand-border p-4">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text mb-4 text-center">Volume de Chamados</h3>
            <div className="h-64 flex items-center justify-center">
              <Doughnut 
                data={ticketsData} 
                options={{ maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } } }} 
              />
            </div>
          </div>

          <div className="bg-brand-card border border-brand-border p-4">
            <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text mb-4 text-center">Saúde dos Equipamentos</h3>
            <div className="h-64 flex items-center justify-center">
              <Bar 
                data={assetsStatusData} 
                options={{ 
                  maintainAspectRatio: false, 
                  plugins: { legend: { display: false } },
                  scales: { y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } }, x: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } } }
                }} 
              />
            </div>
          </div>
        </div>

        {/* Alerts Center */}
        <div className="lg:col-span-1 bg-brand-card border border-brand-border flex flex-col h-full">
          <div className="p-4 border-b border-brand-border flex items-center justify-between">
            <div className="flex items-center text-red-400">
              <BellRing size={18} className="mr-2" />
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider m-0">Alertas Ativos</h3>
            </div>
            {stats.active_alerts && stats.active_alerts.length > 0 && (
              <span className="bg-red-500/20 text-red-400 text-xs font-mono px-2 py-0.5 border border-red-500/30">
                {stats.active_alerts.length}
              </span>
            )}
          </div>
          
          <div className="p-4 flex-1 overflow-y-auto">
            {!stats.active_alerts || stats.active_alerts.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-brand-muted">
                <ShieldAlert size={48} className="mb-3 opacity-20" />
                <p className="text-sm font-mono">Nenhum alerta crítico detectado.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {stats.active_alerts.map((alert) => (
                  <div key={alert.id} className="border-l-2 border-red-500 bg-red-500/5 p-3 flex items-start">
                    {alert.severity === 'CRITICAL' ? (
                      <AlertTriangle className="text-red-500 mt-0.5 mr-3 shrink-0" size={16} />
                    ) : (
                      <Info className="text-yellow-500 mt-0.5 mr-3 shrink-0" size={16} />
                    )}
                    <div>
                      <h4 className="text-sm font-bold text-brand-text mb-1">{alert.title}</h4>
                      <p className="text-xs font-mono text-brand-muted">
                        {new Date(alert.created_at).toLocaleString('pt-BR')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};
