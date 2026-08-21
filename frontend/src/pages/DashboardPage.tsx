import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { dashboardApi } from '../api/dashboard';
import { transactionApi } from '../api/transaction';
import { maintenanceApi } from '../api/maintenance';
import type { DashboardStats } from '../api/dashboard';
import type { Solicitacao, SolicitacaoManutencao } from '../types';
import {
  LayoutDashboard, Wrench, MessageSquare, Briefcase, BellRing, FileDown,
  AlertTriangle, Info, ShieldAlert, Cpu, QrCode, ArrowLeftRight, UserCheck,
  Laptop, Calendar, Clock, X, Send, Paperclip, Star
} from 'lucide-react';
import { serviceDeskApi } from '../api/serviceDesk';
import { toApiFileUrl } from '../api/client';
import type { ServiceTicket } from '../types';


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
  const { user } = useAuthStore();
  const userRole = user?.role?.toLowerCase() || '';
  const isStaff = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico'].includes(userRole);

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const [myActiveLoans, setMyActiveLoans] = useState<Solicitacao[]>([]);
  const [myMaintenanceRequests, setMyMaintenanceRequests] = useState<SolicitacaoManutencao[]>([]);
  const [extraLoading, setExtraLoading] = useState(false);

  // Service desk states for collaborator tracking
  const [myTickets, setMyTickets] = useState<ServiceTicket[]>([]);
  const [selectedDashboardTicket, setSelectedDashboardTicket] = useState<ServiceTicket | null>(null);
  const [commentMessage, setCommentMessage] = useState('');
  const [uploadingAttachment, setUploadingAttachment] = useState(false);

  // Emergency alert modal states for resolved tickets
  const [resolvedTickets, setResolvedTickets] = useState<ServiceTicket[]>([]);
  const [dashboardRating, setDashboardRating] = useState<number>(0);
  const [dashboardHoverRating, setDashboardHoverRating] = useState<number>(0);
  const [dashboardFeedbackComment, setDashboardFeedbackComment] = useState<string>('');
  const [submittingEmergency, setSubmittingEmergency] = useState<boolean>(false);

  useEffect(() => {
    fetchStats();
    if (!isStaff) {
      fetchUserDashboardData();
    }
  }, [isStaff]);

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

  const fetchUserDashboardData = async () => {
    try {
      setExtraLoading(true);
      const [sols, maints, ticketsData] = await Promise.all([
        transactionApi.listSolicitacoes(),
        maintenanceApi.listRequests(),
        serviceDeskApi.listTickets()
      ]);

      const active = sols.filter(s => s.solicitante_id === user?.id && s.status?.toLowerCase() === 'entregue');
      setMyActiveLoans(active);

      const myMaints = maints.filter(m => m.solicitante_id === user?.id);
      setMyMaintenanceRequests(myMaints);

      // Keep only active/open tickets (not status closed/fechado)
      const openTickets = ticketsData.filter(t => t.status?.toLowerCase() !== 'fechado');
      setMyTickets(openTickets);

      // Find tickets with status resolved
      const resolved = ticketsData.filter(t => t.status?.toLowerCase() === 'resolvido');
      setResolvedTickets(resolved);
    } catch (err) {
      console.error('Erro ao buscar dados do dashboard do colaborador:', err);
    } finally {
      setExtraLoading(false);
    }
  };

  const handleConfirmReceipt = async (id: number) => {
    if (!window.confirm('Confirma que recebeu o equipamento consertado e que ele está funcionando corretamente?')) return;
    try {
      setExtraLoading(true);
      await maintenanceApi.confirmReceipt(id);
      await fetchUserDashboardData();
    } catch (err) {
      console.error('Erro ao confirmar recebimento:', err);
      alert('Não foi possível confirmar o recebimento. Tente novamente.');
      setExtraLoading(false);
    }
  };

  // Real-time synchronization (polling) for tickets on collaborator dashboard
  useEffect(() => {
    if (isStaff) return;

    const interval = setInterval(async () => {
      try {
        const ticketsData = await serviceDeskApi.listTickets();
        setMyTickets(ticketsData.filter(t => t.status?.toLowerCase() !== 'fechado'));
        setResolvedTickets(ticketsData.filter(t => t.status?.toLowerCase() === 'resolvido'));
      } catch (err) {
        console.error('Erro ao recarregar chamados em tempo real:', err);
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [isStaff]);

  const handleConfirmEmergencyClose = async (ticketId: number) => {
    try {
      setSubmittingEmergency(true);
      await serviceDeskApi.updateTicket(ticketId, {
        avaliacao: dashboardRating,
        feedback_usuario: dashboardFeedbackComment,
        nota_feedback: dashboardRating,
        comentario_feedback: dashboardFeedbackComment,
        status: 'fechado' as any,
      });

      // Reset emergency states
      setDashboardRating(0);
      setDashboardFeedbackComment('');

      // Refresh user dashboard data
      await fetchUserDashboardData();
    } catch (err) {
      console.error('Erro ao encerrar chamado pelo alerta emergencial:', err);
      alert('Não foi possível encerrar o chamado. Tente novamente.');
    } finally {
      setSubmittingEmergency(false);
    }
  };

  // Real-time synchronization (polling) for the active selected ticket's details/comments
  useEffect(() => {
    if (!selectedDashboardTicket) return;

    const interval = setInterval(async () => {
      try {
        const freshTicket = await serviceDeskApi.getTicketById(selectedDashboardTicket.id);
        setSelectedDashboardTicket(freshTicket);
        // Also update in the local list
        setMyTickets(prev => prev.map(t => t.id === freshTicket.id ? freshTicket : t));
      } catch (err) {
        console.error('Erro ao atualizar chamado no modal:', err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [selectedDashboardTicket?.id]);

  const hasUnreadComments = (ticket: ServiceTicket) => {
    if (!ticket.interacoes || ticket.interacoes.length === 0) return false;
    const lastInteraction = ticket.interacoes[ticket.interacoes.length - 1];

    const author = lastInteraction.usuario || lastInteraction.user;
    if (author && author.id === user?.id) return false;

    const lastReadVal = localStorage.getItem(`ticket_read_${ticket.id}`);
    if (!lastReadVal) return true;

    return Number(lastReadVal) < lastInteraction.id;
  };

  const markTicketAsRead = (ticket: ServiceTicket) => {
    if (ticket.interacoes && ticket.interacoes.length > 0) {
      const lastInteraction = ticket.interacoes[ticket.interacoes.length - 1];
      localStorage.setItem(`ticket_read_${ticket.id}`, String(lastInteraction.id));
    }
  };

  const handleSelectTicket = async (ticket: ServiceTicket) => {
    try {
      const fullTicket = await serviceDeskApi.getTicketById(ticket.id);
      setSelectedDashboardTicket(fullTicket);
      markTicketAsRead(fullTicket);
    } catch (err) {
      console.error('Erro ao carregar detalhes do chamado:', err);
    }
  };

  const handleDashboardPaste = async (e: React.ClipboardEvent<HTMLInputElement>) => {
    const items = e.clipboardData?.items;
    if (!items || !selectedDashboardTicket) return;
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile();
        if (file) {
          e.preventDefault();
          try {
            setUploadingAttachment(true);
            const res = await serviceDeskApi.uploadAttachment(selectedDashboardTicket.id, file);
            const finalMsg = `Enviou uma imagem colada: ${file.name}`;
            await serviceDeskApi.createInteraction(selectedDashboardTicket.id, finalMsg, res.url);

            const freshTicket = await serviceDeskApi.getTicketById(selectedDashboardTicket.id);
            setSelectedDashboardTicket(freshTicket);
            setMyTickets(prev => prev.map(t => t.id === freshTicket.id ? freshTicket : t));
          } catch (err) {
            alert('Erro ao colar/enviar anexo.');
          } finally {
            setUploadingAttachment(false);
          }
          break;
        }
      }
    }
  };

  const handleDashboardFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0 && selectedDashboardTicket) {
      const file = e.target.files[0];
      try {
        setUploadingAttachment(true);
        const res = await serviceDeskApi.uploadAttachment(selectedDashboardTicket.id, file);
        const finalMsg = `Enviou um anexo: ${file.name}`;
        await serviceDeskApi.createInteraction(selectedDashboardTicket.id, finalMsg, res.url);

        const freshTicket = await serviceDeskApi.getTicketById(selectedDashboardTicket.id);
        setSelectedDashboardTicket(freshTicket);
        setMyTickets(prev => prev.map(t => t.id === freshTicket.id ? freshTicket : t));
      } catch (err) {
        alert('Erro ao fazer upload do anexo.');
      } finally {
        setUploadingAttachment(false);
      }
    }
  };

  const handleSendDashboardComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDashboardTicket || !commentMessage.trim()) return;

    try {
      await serviceDeskApi.createInteraction(selectedDashboardTicket.id, commentMessage);
      setCommentMessage('');

      const freshTicket = await serviceDeskApi.getTicketById(selectedDashboardTicket.id);
      setSelectedDashboardTicket(freshTicket);
      setMyTickets(prev => prev.map(t => t.id === freshTicket.id ? freshTicket : t));
    } catch (err) {
      alert('Erro ao enviar mensagem.');
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
          ['Ativos em Manutenção', String(stats?.total_assets_maintenance || 0)],
          ['Ativos Disponíveis', String(stats?.total_assets_disponivel || 0)],
          ['Ativos Em Uso', String(stats?.total_assets_em_uso || 0)],
          ['Ativos Armazenados', String(stats?.total_assets_armazenado || 0)],
          ['Ativos Baixados', String(stats?.total_assets_baixado || 0)],
          ['Chamados Abertos vs Resolvidos', `${stats?.tickets_open || 0} Abertos / ${stats?.tickets_resolved || 0} Resolvidos / ${stats?.tickets_closed || 0} Fechados`],
          ['Solicitações de Ativos (Pendentes)', String(stats?.pending_asset_requests || 0)],
          ['Custo Mensal Fornecedores', `R$ ${(stats?.supplier_cost_monthly || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`],
        ]
      });

      // Alerts
      const currentY = (doc as any).lastAutoTable.finalY + 15;
      doc.text('Alertas Ativos', 14, currentY);

      if (stats?.active_alerts && stats.active_alerts.length > 0) {
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
    labels: ['Abertos', 'Resolvidos', 'Fechados'],
    datasets: [
      {
        data: [
          stats?.tickets_open || 0,
          stats?.tickets_resolved || 0,
          stats?.tickets_closed || 0
        ],
        backgroundColor: [
          'rgba(239, 68, 68, 0.8)', // red-500
          'rgba(245, 158, 11, 0.8)', // amber-500
          'rgba(34, 197, 94, 0.8)', // green-500
        ],
        borderColor: [
          'rgba(239, 68, 68, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(34, 197, 94, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const assetsStatusData = {
    labels: ['Disponível', 'Em Uso', 'Manutenção', 'Armazenado', 'Baixado'],
    datasets: [
      {
        label: 'Quantidade',
        data: [
          stats?.total_assets_disponivel || 0,
          stats?.total_assets_em_uso || 0,
          stats?.total_assets_maintenance || 0,
          stats?.total_assets_armazenado || 0,
          stats?.total_assets_baixado || 0
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.5)',  // green-500
          'rgba(59, 130, 246, 0.5)',  // blue-500
          'rgba(245, 158, 11, 0.5)',  // amber-500
          'rgba(107, 114, 128, 0.5)', // gray-500
          'rgba(239, 68, 68, 0.5)'    // red-500
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(107, 114, 128, 1)',
          'rgba(239, 68, 68, 1)'
        ],
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
            {isStaff ? 'Painel Executivo' : `Portal do Colaborador (${user?.nome})`}
          </h1>
          <p className="text-brand-muted text-sm mt-1">
            {isStaff
              ? 'Visão geral do ecossistema de TI, métricas e análises'
              : 'Gerencie seus chamados de TI, solicitações de equipamentos e crachá digital'}
          </p>
        </div>
        {isStaff && (
          <button
            onClick={exportPDF}
            disabled={exporting}
            className="rounded-[10px] bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-sm flex items-center hover:bg-brand-primary/90 transition-colors shadow-lg shadow-brand-primary/20 disabled:opacity-50"
          >
            <FileDown size={18} className="mr-2" />
            {exporting ? 'Gerando...' : 'Exportar Relatório PDF'}
          </button>
        )}
      </div>

      {/* Alert Banner for Pending Asset Requests (Staff/Managers) */}
      {isStaff && stats.pending_asset_requests > 0 && (
        <div className="bg-amber-500/10 border-l-4 border-amber-500 p-4 flex items-center justify-between shadow-lg">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-amber-500/20 text-amber-400 rounded">
              <AlertTriangle size={24} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-amber-300 uppercase tracking-wider font-mono">
                Atenção: {stats.pending_asset_requests} {stats.pending_asset_requests === 1 ? 'Solicitação de Ativo Pendente' : 'Solicitações de Ativos Pendentes'}
              </h3>
              <p className="text-xs text-brand-muted mt-0.5">
                Existem solicitações de empréstimo de equipamentos aguardando aprovação ou confirmação de entrega.
              </p>
            </div>
          </div>
          <Link
            to="/emprestimos"
            className="px-4 py-2 bg-amber-500 text-brand-dark font-bold text-xs uppercase tracking-wider font-mono hover:bg-amber-400 transition-all shrink-0"
          >
            Analisar Solicitações
          </Link>
        </div>
      )}

      {/* Alert Banner for Pending Maintenance Requests (Staff/Managers) */}
      {isStaff && stats.pending_maintenance_requests > 0 && (
        <div className="bg-red-500/10 border-l-4 border-red-500 p-4 flex items-center justify-between shadow-lg">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-500/20 text-red-400 rounded">
              <AlertTriangle size={24} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-red-300 uppercase tracking-wider font-mono">
                Atenção: {stats.pending_maintenance_requests} {stats.pending_maintenance_requests === 1 ? 'Solicitação de Manutenção Pendente' : 'Solicitações de Manutenção Pendentes'}
              </h3>
              <p className="text-xs text-brand-muted mt-0.5">
                Existem solicitações de manutenção aguardando atendimento ou resposta técnica.
              </p>
            </div>
          </div>
          <Link
            to="/manutencoes"
            className="px-4 py-2 bg-red-500 text-brand-dark font-bold text-xs uppercase tracking-wider font-mono hover:bg-red-400 transition-all shrink-0"
          >
            Analisar Manutenções
          </Link>
        </div>
      )}

      {!isStaff ? (
        /* Portal do Colaborador Layout */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link
              to="/servicos"
              className="p-6 bg-brand-card border border-brand-border hover:border-brand-primary/50 transition-all group flex flex-col justify-between space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="p-3 bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <MessageSquare size={28} />
                </div>
                <span className="text-xs font-mono text-brand-muted group-hover:text-brand-primary transition-colors">Acessar →</span>
              </div>
              <div>
                <h3 className="font-bold text-brand-text text-lg group-hover:text-brand-primary transition-colors">Central de Suporte</h3>
                <p className="text-xs text-brand-muted mt-1">Abra chamados para suporte técnico, incidentes ou dúvidas com a equipe de TI.</p>
              </div>
            </Link>

            <Link
              to="/emprestimos"
              className="p-6 bg-brand-card border border-brand-border hover:border-brand-primary/50 transition-all group flex flex-col justify-between space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="p-3 bg-purple-500/10 text-purple-400 border border-purple-500/20">
                  <ArrowLeftRight size={28} />
                </div>
                <span className="text-xs font-mono text-brand-muted group-hover:text-brand-primary transition-colors">Acessar →</span>
              </div>
              <div>
                <h3 className="font-bold text-brand-text text-lg group-hover:text-brand-primary transition-colors">Solicitar Equipamento</h3>
                <p className="text-xs text-brand-muted mt-1">Solicite empréstimos temporários de notebooks, periféricos ou dispositivos.</p>
              </div>
            </Link>

            <Link
              to="/badge"
              className="p-6 bg-brand-card border border-brand-border hover:border-brand-primary/50 transition-all group flex flex-col justify-between space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="p-3 bg-brand-primary/10 text-brand-primary border border-brand-primary/20">
                  <QrCode size={28} />
                </div>
                <span className="text-xs font-mono text-brand-muted group-hover:text-brand-primary transition-colors">Acessar →</span>
              </div>
              <div>
                <h3 className="font-bold text-brand-text text-lg group-hover:text-brand-primary transition-colors">Meu Crachá QR</h3>
                <p className="text-xs text-brand-muted mt-1">Visualize seu token QR pessoal para identificação e retirada rápida de ativos.</p>
              </div>
            </Link>
          </div>

          {/* Real-time Support reply notification banner */}
          {myTickets.some(hasUnreadComments) && (
            <div className="bg-brand-primary/10 border-l-4 border-brand-primary p-4 mb-6 flex items-center justify-between animate-pulse">
              <div className="flex items-center space-x-3">
                <MessageSquare className="text-brand-primary shrink-0" size={20} />
                <div>
                  <h4 className="text-xs font-bold text-brand-primary uppercase tracking-wider font-mono">
                    Nova resposta do suporte técnico!
                  </h4>
                  <p className="text-[14px] text-black mt-1">
                    Você possui novas mensagens não lidas nos seus chamados ativos. Clique no chamado abaixo para visualizar e responder.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Active Loans & Maintenance Tracking & Support Tickets */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Active Assets Block */}
            <div className="bg-brand-card border border-brand-border p-6 space-y-4">
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-muted flex items-center space-x-2">
                <Laptop size={18} className="text-brand-primary" />
                <span>Meus Equipamentos em Posse</span>
              </h3>

              {extraLoading ? (
                <div className="text-xs text-brand-muted font-mono">Carregando seus ativos...</div>
              ) : myActiveLoans.length === 0 ? (
                <div className="text-xs text-brand-muted bg-brand-dark/20 p-4 border border-brand-border/40 text-center">
                  Você não possui nenhum equipamento emprestado no momento.
                </div>
              ) : (
                <div className="space-y-3">
                  {myActiveLoans.map(loan => {
                    const hasActiveMaint = myMaintenanceRequests.some(
                      req => req.asset_id === loan.asset_id &&
                        !['concluida', 'rejeitada'].includes(req.status?.toLowerCase() || '')
                    );

                    return (
                      <div key={loan.id} className="p-4 bg-brand-dark/40 border border-brand-border/60 flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold text-brand-text text-sm">{loan.asset?.nome || 'Equipamento'}</h4>
                          <p className="text-[11px] text-brand-muted font-mono mt-0.5">
                            EP: {loan.asset?.e_patrimonio} {loan.asset?.modelo ? ` · ${loan.asset.modelo}` : ''}
                          </p>
                          <p className="text-[10px] text-brand-muted font-mono mt-1 flex items-center space-x-1">
                            <Calendar size={10} />
                            <span>Entregue em: {loan.data_entrega ? new Date(loan.data_entrega).toLocaleDateString('pt-BR') : '-'}</span>
                          </p>
                        </div>
                        {!hasActiveMaint ? (
                          <Link
                            to="/emprestimos"
                            className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-brand-dark font-bold text-xs uppercase tracking-wider font-mono flex items-center space-x-1 transition-all"
                          >
                            <Wrench size={12} />
                            <span>Manutenção</span>
                          </Link>
                        ) : (
                          <div className="px-3 py-1 border border-amber-500/30 text-amber-500 font-bold text-xs uppercase tracking-wider font-mono flex items-center space-x-1 opacity-60">
                            <Wrench size={12} />
                            <span>Em Andamento</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* Maintenance Requests Block */}
            <div className="bg-brand-card border border-brand-border p-6 space-y-4">
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-muted flex items-center space-x-2">
                <Wrench size={18} className="text-amber-500" />
                <span>Solicitações de Manutenção</span>
              </h3>

              {extraLoading ? (
                <div className="text-xs text-brand-muted font-mono">Carregando solicitações...</div>
              ) : myMaintenanceRequests.length === 0 ? (
                <div className="text-xs text-brand-muted bg-brand-dark/20 p-4 border border-brand-border/40 text-center">
                  Nenhuma solicitação de manutenção em aberto ou concluída.
                </div>
              ) : (
                <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
                  {myMaintenanceRequests.map(req => {
                    const statusLower = req.status?.toLowerCase() || '';
                    let statusColor = '';
                    let statusLabel = '';

                    if (statusLower === 'pendente') {
                      statusColor = 'text-blue-400 bg-blue-400/10 border-blue-400/20';
                      statusLabel = 'Pendente';
                    } else if (statusLower === 'aceita' || statusLower === 'em_andamento') {
                      statusColor = 'text-amber-400 bg-amber-400/10 border-amber-400/20';
                      statusLabel = 'Em Manutenção';
                    } else if (statusLower === 'aguardando_entrega' || statusLower === 'concluida') {
                      statusColor = 'text-brand-primary bg-brand-primary/10 border-brand-primary/20';
                      statusLabel = statusLower === 'concluida' ? 'Concluída' : 'Pronto p/ Retirada';
                    } else if (statusLower === 'rejeitada') {
                      statusColor = 'text-red-400 bg-red-400/10 border-red-400/20';
                      statusLabel = 'Rejeitada';
                    } else {
                      statusLabel = req.status || '';
                    }

                    return (
                      <div key={req.id} className="p-4 bg-brand-dark/40 border border-brand-border/60 flex flex-col justify-between space-y-2">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold text-brand-text text-xs">{req.asset?.nome || 'Equipamento'}</h4>
                            <p className="text-[10px] text-brand-muted font-mono mt-0.5">EP: {req.asset?.e_patrimonio}</p>
                          </div>
                          <span className={`text-[9px] uppercase font-bold px-1.5 py-0.5 border ${statusColor}`}>
                            {statusLabel}
                          </span>
                        </div>
                        <div className="text-[11px] text-brand-muted bg-brand-dark/60 p-2 border border-brand-border/30 rounded font-mono truncate">
                          Defeito: "{req.descricao}"
                        </div>
                        <div className="flex justify-between items-center mt-2">
                          {req.data_resposta ? (
                            <div className="text-[9px] text-brand-muted font-mono flex items-center space-x-1">
                              <Clock size={10} />
                              <span>Respondido em: {new Date(req.data_resposta).toLocaleDateString('pt-BR')}</span>
                            </div>
                          ) : (
                            <div />
                          )}

                          {statusLower === 'aguardando_entrega' && (
                            <button
                              onClick={() => handleConfirmReceipt(req.id)}
                              className="px-2 py-1 bg-brand-primary text-brand-dark font-bold text-[9px] uppercase tracking-wider font-mono hover:bg-brand-primary/90 transition-all ml-2 shrink-0 shadow shadow-brand-primary/20"
                            >
                              Confirmar Recebimento
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Active Tickets Block */}
            <div className={`bg-brand-card border p-6 space-y-4 transition-all duration-300 ${myTickets.some(hasUnreadComments) ? 'border-brand-primary/40 shadow-[0_0_15px_rgba(245,158,11,0.05)]' : 'border-brand-border'
              }`}>
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-muted flex items-center justify-between w-full">
                <div className="flex items-center space-x-2">
                  <MessageSquare size={18} className="text-brand-primary" />
                  <span>Chamados de Suporte Ativos</span>
                </div>
                {myTickets.filter(hasUnreadComments).length > 0 && (
                  <span className="text-[9px] bg-brand-primary text-brand-dark font-black px-2 py-0.5 animate-bounce">
                    {myTickets.filter(hasUnreadComments).length} NOVO(S)
                  </span>
                )}
              </h3>

              {extraLoading ? (
                <div className="text-xs text-brand-muted font-mono">Carregando chamados...</div>
              ) : myTickets.length === 0 ? (
                <div className="text-xs text-brand-muted bg-brand-dark/20 p-4 border border-brand-border/40 text-center">
                  Nenhum chamado de suporte ativo.
                </div>
              ) : (
                <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
                  {myTickets.map(ticket => {
                    const hasUnread = hasUnreadComments(ticket);
                    const statusLower = ticket.status?.toLowerCase() || '';
                    let statusColor = 'text-brand-muted bg-brand-dark border-brand-border';
                    if (statusLower === 'aberto') {
                      statusColor = 'text-blue-400 bg-blue-400/10 border-blue-400/20';
                    } else if (statusLower === 'em_atendimento') {
                      statusColor = 'text-amber-400 bg-amber-400/10 border-amber-400/20';
                    } else if (statusLower === 'resolvido') {
                      statusColor = 'text-brand-primary bg-brand-primary/10 border-brand-primary/20';
                    }

                    return (
                      <div
                        key={ticket.id}
                        onClick={() => handleSelectTicket(ticket)}
                        className={`p-4 bg-brand-dark/40 border transition-all duration-150 cursor-pointer flex flex-col justify-between space-y-2 hover:border-brand-primary/45 relative ${hasUnread ? 'border-brand-primary bg-brand-primary/5' : 'border-brand-border/60'
                          }`}
                      >
                        {hasUnread && (
                          <div className="absolute top-2 right-2 flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-primary opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-primary"></span>
                          </div>
                        )}
                        <div className="flex justify-between items-start">
                          <div>
                            <div className="flex items-center space-x-1.5">
                              <span className="text-[9px] font-mono font-bold text-brand-primary px-1 py-0.2 bg-brand-primary/10 border border-brand-primary/20 shrink-0">
                                {ticket.codigo}
                              </span>
                              <h4 className="font-semibold text-brand-text text-xs line-clamp-1">{ticket.titulo}</h4>
                            </div>
                            <p className="text-[10px] text-brand-muted font-mono mt-1 flex items-center space-x-1">
                              <Clock size={10} />
                              <span>Atualizado: {new Date(ticket.data_abertura).toLocaleDateString('pt-BR')}</span>
                            </p>
                          </div>
                          <span className={`text-[8px] uppercase font-bold px-1.5 py-0.5 border ${statusColor} shrink-0`}>
                            {ticket.status.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="text-[11px] text-brand-muted bg-brand-dark/60 p-2 border border-brand-border/30 rounded font-mono truncate">
                          "{ticket.descricao}"
                        </div>
                        <div className="flex justify-between items-center pt-1">
                          {hasUnread ? (
                            <span className="text-[9px] font-bold text-brand-primary animate-pulse flex items-center space-x-1">
                              <span>💬</span>
                              <span>Novas respostas!</span>
                            </span>
                          ) : (
                            <div />
                          )}
                          <button
                            type="button"
                            className="text-[9px] font-bold text-brand-primary hover:underline flex items-center space-x-0.5 ml-auto"
                          >
                            <span>Responder</span>
                            <span>→</span>
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

          </div>

          <div className="p-6 bg-brand-card border border-brand-border flex items-center space-x-4">
            <div className="p-3 bg-brand-primary/10 text-brand-primary border border-brand-primary/20 shrink-0">
              <UserCheck size={24} />
            </div>
            <div>
              <h4 className="font-semibold text-brand-text text-sm">Status do Seu Perfil ({user?.role.replace('_', ' ')})</h4>
              <p className="text-sm text-brand-muted mt-0.5">Você está com perfil de colaborador ativo. Para alteração de permissões ou acesso administrativo, entre em contato com a equipe de TI.</p>
            </div>
          </div>
        </div>

      ) : (
        /* Executive Dashboard Layout (Staff/Admin) */
        <>
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
                <div className="text-[11px] font-mono text-green-400">
                  / {stats.tickets_resolved} resolvidos · {stats.tickets_closed} fechados
                </div>
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
        </>
      )}

      {isStaff && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Charts */}
          <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-brand-card border border-brand-border p-4 opacity-80">
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text mb-4 text-center">Volume de Chamados</h3>
              <div className="h-64 flex items-center justify-center">
                <Doughnut
                  data={ticketsData}
                  options={{ maintainAspectRatio: false, cutout: '70%', plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } } } }}
                />
              </div>
            </div>

            <div className="bg-brand-card border border-brand-border p-4 opacity-80">
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
          <div className="lg:col-span-1 bg-brand-card border border-brand-border flex flex-col h-full opacity-80">
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
      )}

      {selectedDashboardTicket && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-2xl bg-brand-card border border-brand-border shadow-2xl flex flex-col max-h-[85vh] rounded-none">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border bg-brand-dark/50">
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono font-bold text-brand-primary px-1.5 py-0.5 bg-brand-primary/10 border border-brand-primary/20">
                  {selectedDashboardTicket.codigo}
                </span>
                <h3 className="font-semibold text-sm text-brand-text truncate max-w-md">
                  {selectedDashboardTicket.titulo}
                </h3>
              </div>
              <button
                onClick={() => setSelectedDashboardTicket(null)}
                className="text-brand-muted hover:text-brand-text transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Content/Timeline */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="bg-brand-dark/30 p-4 border border-brand-border/40 space-y-2">
                <div className="flex justify-between items-center text-xs text-brand-muted">
                  <span>Aberto em: {new Date(selectedDashboardTicket.data_abertura).toLocaleString('pt-BR')}</span>
                  <span className="px-1.5 py-0.5 bg-brand-dark border border-brand-border text-brand-muted uppercase text-[9px] font-bold">
                    {selectedDashboardTicket.status}
                  </span>
                </div>
                <p className="text-sm text-brand-text whitespace-pre-wrap">{selectedDashboardTicket.descricao}</p>
                {selectedDashboardTicket.foto && (
                  <div className="mt-2 pt-2 border-t border-brand-border/20">
                    <span className="text-[10px] text-brand-muted block mb-1">Anexo Inicial:</span>
                    <a href={toApiFileUrl(selectedDashboardTicket.foto)} target="_blank" rel="noreferrer" className="block max-w-max">
                      <img
                        src={toApiFileUrl(selectedDashboardTicket.foto)}
                        alt="Anexo"
                        className="max-h-32 max-w-full rounded-none border border-brand-border/60 hover:border-brand-primary/60 transition-colors"
                      />
                    </a>
                  </div>
                )}
              </div>

              {/* Interactions List */}
              <div className="space-y-4 pt-2">
                <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-brand-muted flex items-center space-x-1.5">
                  <MessageSquare size={14} />
                  <span>Interações e Histórico</span>
                </h4>

                {!selectedDashboardTicket.interacoes || selectedDashboardTicket.interacoes.length === 0 ? (
                  <div className="text-xs text-brand-muted font-mono italic text-center py-4 bg-brand-dark/20 border border-brand-border/30">
                    Nenhuma interação registrada ainda.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {selectedDashboardTicket.interacoes.map((item) => {
                      const author = item.usuario || item.user;
                      const isMe = author?.id === user?.id;

                      return (
                        <div
                          key={item.id}
                          className={`p-3 border flex flex-col space-y-1.5 ${isMe
                              ? 'border-brand-primary/20 bg-brand-primary/5 ml-8'
                              : 'border-brand-border/60 bg-brand-dark/40 mr-8'
                            }`}
                        >
                          <div className="flex justify-between items-center text-[10px] text-brand-muted">
                            <span className="font-semibold text-brand-text">
                              {author?.nome || 'Usuário'} ({author?.id === selectedDashboardTicket.solicitante_id ? 'Solicitante' : 'Suporte'})
                            </span>
                            <span>{new Date(item.data_criacao).toLocaleString('pt-BR')}</span>
                          </div>
                          <p className="text-xs text-brand-text whitespace-pre-wrap">{item.mensagem}</p>
                          {item.foto && (
                            <div className="mt-1.5 pt-1.5 border-t border-brand-border/20">
                              {item.foto.toLowerCase().endsWith('.png') ||
                                item.foto.toLowerCase().endsWith('.jpg') ||
                                item.foto.toLowerCase().endsWith('.jpeg') ||
                                item.foto.toLowerCase().endsWith('.gif') ||
                                item.foto.toLowerCase().endsWith('.webp') ? (
                                <a href={toApiFileUrl(item.foto)} target="_blank" rel="noreferrer" className="block max-w-max">
                                  <img
                                    src={toApiFileUrl(item.foto)}
                                    alt="Anexo"
                                    className="max-h-32 max-w-full border border-brand-border/60"
                                  />
                                </a>
                              ) : (
                                <a
                                  href={toApiFileUrl(item.foto)}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center space-x-1.5 text-brand-primary hover:underline text-[11px]"
                                >
                                  <span>📎</span>
                                  <span className="underline">{item.foto.split('/').pop()}</span>
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Footer Input Area */}
            {selectedDashboardTicket.status?.toLowerCase() !== 'fechado' && (
              <div className="p-4 border-t border-brand-border bg-brand-dark/50">
                <form onSubmit={handleSendDashboardComment} className="flex items-center space-x-2">
                  <input
                    type="text"
                    placeholder="Escreva uma resposta... (Ctrl+V para colar imagem)"
                    value={commentMessage}
                    onChange={(e) => setCommentMessage(e.target.value)}
                    onPaste={handleDashboardPaste}
                    className="flex-1 bg-brand-dark border border-brand-border px-3 py-2 text-xs focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/40 rounded-none"
                  />

                  <label className="p-2 bg-brand-dark border border-brand-border text-brand-muted hover:text-brand-text hover:border-brand-primary/50 transition-all cursor-pointer flex items-center justify-center shrink-0">
                    <Paperclip size={14} />
                    <input
                      type="file"
                      onChange={handleDashboardFileChange}
                      className="hidden"
                      accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar"
                    />
                  </label>

                  <button
                    type="submit"
                    disabled={uploadingAttachment || !commentMessage.trim()}
                    className="p-2 bg-brand-primary/10 border border-brand-primary/30 text-brand-primary hover:bg-brand-primary hover:text-brand-dark transition-all disabled:opacity-40 flex items-center justify-center shrink-0"
                  >
                    {uploadingAttachment ? (
                      <span className="animate-spin inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full" />
                    ) : (
                      <Send size={14} />
                    )}
                  </button>
                </form>
                {uploadingAttachment && (
                  <div className="text-[10px] text-brand-primary font-mono animate-pulse mt-1">
                    Enviando anexo...
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {resolvedTickets.length > 0 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/95 backdrop-blur-xl">
          {/* Main Emergency Container */}
          <div className="w-full max-w-lg bg-slate-950 border-4 border-amber-500 shadow-2xl relative flex flex-col overflow-hidden rounded-none">
            {/* Caution Stripes Top */}
            <div className="h-4 bg-amber-500 animate-pulse" style={{
              backgroundImage: 'repeating-linear-gradient(-45deg, #f59e0b, #f59e0b 10px, #000 10px, #000 20px)'
            }} />

            {/* Content Box */}
            <div className="p-8 space-y-6 text-center">
              {/* Flashing Warning Beacon */}
              <div className="mx-auto flex items-center justify-center h-20 w-20 rounded-full bg-amber-500/10 border-2 border-amber-500 animate-pulse relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-500/20 opacity-75"></span>
                <AlertTriangle size={42} className="text-amber-500 animate-bounce" />
              </div>

              {/* Title & Info */}
              <div className="space-y-2">
                <h2 className="text-xl font-black font-mono tracking-widest text-amber-500 uppercase">
                  Alerta do Sistema: Chamado Concluído!
                </h2>
                <div className="text-xs font-mono text-slate-400 uppercase tracking-wider flex items-center justify-center space-x-2">
                  <span className="text-brand-primary font-bold px-1.5 py-0.5 bg-brand-primary/10 border border-brand-primary/20">
                    {resolvedTickets[0].codigo}
                  </span>
                  <span>—</span>
                  <span className="text-slate-200 font-bold truncate max-w-[200px]">{resolvedTickets[0].titulo}</span>
                </div>
              </div>

              <div className="bg-slate-900 p-5 border border-slate-800 text-left rounded-none space-y-2">
                <p className="text-[10px] uppercase font-mono tracking-wider text-amber-500 font-bold">Nota de Solução do Técnico:</p>
                <div className="text-xs font-mono text-slate-100 italic bg-slate-950 p-4 border border-slate-800 leading-relaxed">
                  "{resolvedTickets[0].solucao || resolvedTickets[0].nota_resolucao || 'O chamado foi resolvido e está pronto para encerramento.'}"
                </div>
              </div>

              {/* Rate and comment */}
              <div className="space-y-4 pt-2">
                <p className="text-xs font-bold font-mono tracking-wide text-slate-200 uppercase">
                  Por favor, avalie o atendimento antes de encerrar:
                </p>

                {/* Stars Component with Hover and Selection */}
                <div className="flex justify-center items-center space-x-2">
                  {[1, 2, 3, 4, 5].map((star) => {
                    const isLit = star <= (dashboardHoverRating || dashboardRating);
                    return (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setDashboardRating(star)}
                        onMouseEnter={() => setDashboardHoverRating(star)}
                        onMouseLeave={() => setDashboardHoverRating(0)}
                        className="transition-all transform hover:scale-125 focus:outline-none"
                      >
                        <Star
                          size={32}
                          className={`transition-colors duration-100 ${isLit
                              ? 'text-amber-400 fill-amber-400 filter drop-shadow-[0_0_8px_rgba(245,158,11,0.6)]'
                              : 'text-slate-700 hover:text-amber-400'
                            }`}
                        />
                      </button>
                    );
                  })}
                </div>

                {/* Comment Input */}
                <div className="space-y-1.5 text-left">
                  <label className="text-[10px] font-mono text-slate-400 uppercase font-bold">Deixe seu comentário / feedback (opcional):</label>
                  <textarea
                    rows={2}
                    placeholder="Escreva algo sobre o atendimento..."
                    value={dashboardFeedbackComment}
                    onChange={(e) => setDashboardFeedbackComment(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 px-3 py-2 text-xs focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500 text-slate-100 placeholder-slate-500 rounded-none resize-none"
                  />
                </div>
              </div>

              {/* Confirm / Close Button */}
              <div className="pt-2">
                <button
                  type="button"
                  disabled={submittingEmergency}
                  onClick={() => handleConfirmEmergencyClose(resolvedTickets[0].id)}
                  className="w-full py-3 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-black font-black text-xs uppercase tracking-widest font-mono transition-all border-none focus:outline-none flex items-center justify-center space-x-2 shadow-lg shadow-amber-500/20"
                >
                  {submittingEmergency ? (
                    <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
                  ) : (
                    <>
                      <span>Confirmar Avaliação e Encerrar Chamado</span>
                      <span>🚀</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Caution Stripes Bottom */}
            <div className="h-4 bg-amber-500" style={{
              backgroundImage: 'repeating-linear-gradient(-45deg, #f59e0b, #f59e0b 10px, #000 10px, #000 20px)'
            }} />
          </div>
        </div>
      )}
    </div>
  );
};
