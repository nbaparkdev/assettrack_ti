import React, { useState, useEffect } from 'react';
import { serviceDeskApi } from '../api/serviceDesk';
import { usersApi } from '../api/users';
import { useAuthStore } from '../stores/authStore';
import type { ServiceTicket, ServiceCategory, ServiceDefinition, User } from '../types';
import { 
  Plus, 
  MessageSquare, 
  Clock, 
  User as UserIcon, 
  Check, 
  X, 
  AlertCircle, 
  Filter, 
  CheckCircle2, 
  Send,
  Star
} from 'lucide-react';

export const ServiceDeskPage: React.FC = () => {
  const { user: currentUser } = useAuthStore();
  const isTechnicianOrAbove = currentUser?.role === 'admin' || currentUser?.role === 'gerente_ti' || currentUser?.role === 'tecnico';

  const [tickets, setTickets] = useState<ServiceTicket[]>([]);
  const [categories, setCategories] = useState<ServiceCategory[]>([]);
  const [definitions, setDefinitions] = useState<ServiceDefinition[]>([]);
  const [technicians, setTechnicians] = useState<User[]>([]);
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters state
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');

  // Ticket creation form
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newPriority, setNewPriority] = useState<'baixa' | 'media' | 'alta' | 'urgente'>('media');
  const [selectedDefinitionId, setSelectedDefinitionId] = useState<number | ''>('');

  // Config modal state
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [activeConfigTab, setActiveConfigTab] = useState<'categorias' | 'servicos'>('categorias');
  
  // Category form
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDesc, setNewCategoryDesc] = useState('');
  
  // Definition form
  const [newDefName, setNewDefName] = useState('');
  const [newDefDesc, setNewDefDesc] = useState('');
  const [newDefCategoryId, setNewDefCategoryId] = useState<number | ''>('');
  // Detail panel state (Layout Diversification: Slide-out panel)
  const [selectedTicket, setSelectedTicket] = useState<ServiceTicket | null>(null);
  const [commentMessage, setCommentMessage] = useState('');
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [showResolutionForm, setShowResolutionForm] = useState(false);
  const [rating, setRating] = useState<number>(5);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  
  // Assign state
  const [assignedTechId, setAssignedTechId] = useState<number | ''>('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const ticketsData = await serviceDeskApi.listTickets();
      setTickets(ticketsData);
      
      const catsData = await serviceDeskApi.listCategories();
      setCategories(catsData);
      
      const defsData = await serviceDeskApi.listDefinitions();
      setDefinitions(defsData);

      if (isTechnicianOrAbove) {
        const usersData = await usersApi.list();
        // filter technicians
        const techs = usersData.filter(u => u.role === 'tecnico' || u.role === 'admin' || u.role === 'gerente_ti');
        setTechnicians(techs);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar dados do Service Desk.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newDescription || !selectedDefinitionId) {
      setError('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    try {
      const ticket = await serviceDeskApi.createTicket({
        titulo: newTitle,
        descricao: newDescription,
        prioridade: newPriority,
        servico_id: Number(selectedDefinitionId),
      });

      setTickets([ticket, ...tickets]);
      setShowCreateModal(false);
      // Reset form
      setNewTitle('');
      setNewDescription('');
      setNewPriority('media');
      setSelectedDefinitionId('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao abrir chamado.');
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategoryName) return;
    try {
      const cat = await serviceDeskApi.createCategory({
        nome: newCategoryName,
        descricao: newCategoryDesc
      });
      setCategories([...categories, cat]);
      setNewCategoryName('');
      setNewCategoryDesc('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao criar categoria.');
    }
  };

  const handleCreateDefinition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDefName || !newDefCategoryId) return;
    try {
      const def = await serviceDeskApi.createDefinition({
        nome: newDefName,
        descricao: newDefDesc,
        categoria_id: Number(newDefCategoryId)
      });
      setDefinitions([...definitions, def]);
      setNewDefName('');
      setNewDefDesc('');
      setNewDefCategoryId('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao criar serviço.');
    }
  };

  const handleSendComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket || !commentMessage.trim()) return;

    try {
      const newComment = await serviceDeskApi.createInteraction(selectedTicket.id, commentMessage);
      
      const updatedTicket = { ...selectedTicket };
      updatedTicket.interacoes = [...(updatedTicket.interacoes || []), newComment];
      
      setSelectedTicket(updatedTicket);
      setTickets(tickets.map(t => t.id === updatedTicket.id ? updatedTicket : t));
      setCommentMessage('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao enviar comentário.');
    }
  };

  const handleUpdateStatus = async (status: 'em_atendimento' | 'resolvido' | 'fechado', notes?: string) => {
    if (!selectedTicket) return;

    try {
      const payload: Partial<ServiceTicket> = { status };
      if (notes) {
        payload.nota_resolucao = notes;
      }
      if (assignedTechId) {
        payload.tecnico_id = Number(assignedTechId);
        payload.responsavel_id = Number(assignedTechId);
      }

      const updated = await serviceDeskApi.updateTicket(selectedTicket.id, payload);
      
      // reload full details to get interactions
      const freshTicket = await serviceDeskApi.getTicketById(updated.id);
      setSelectedTicket(freshTicket);
      setTickets(tickets.map(t => t.id === freshTicket.id ? freshTicket : t));
      
      setShowResolutionForm(false);
      setResolutionNotes('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao atualizar status do chamado.');
    }
  };

  const handleAssignTicket = async (techId: number) => {
    if (!selectedTicket) return;
    try {
      const updated = await serviceDeskApi.updateTicket(selectedTicket.id, {
        tecnico_id: techId,
        responsavel_id: techId,
        status: 'em_atendimento',
      });
      const freshTicket = await serviceDeskApi.getTicketById(updated.id);
      setSelectedTicket(freshTicket);
      setTickets(tickets.map(t => t.id === freshTicket.id ? freshTicket : t));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao delegar chamado.');
    }
  };

  const handleSendFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTicket) return;

    try {
      const updated = await serviceDeskApi.updateTicket(selectedTicket.id, {
        avaliacao: rating,
        feedback_usuario: feedbackComment,
        nota_feedback: rating,
        comentario_feedback: feedbackComment,
        status: 'fechado' as any,
      });
      const freshTicket = await serviceDeskApi.getTicketById(updated.id);
      setSelectedTicket(freshTicket);
      setTickets(tickets.map(t => t.id === freshTicket.id ? freshTicket : t));
      setShowFeedbackForm(false);
      setFeedbackComment('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao enviar feedback.');
    }
  };

  const handleSelectTicket = async (ticket: ServiceTicket) => {
    try {
      const fullTicket = await serviceDeskApi.getTicketById(ticket.id);
      setSelectedTicket(fullTicket);
      if (fullTicket.responsavel_id) {
        setAssignedTechId(fullTicket.responsavel_id);
      } else {
        setAssignedTechId('');
      }
    } catch (err: any) {
      setError('Erro ao carregar detalhes do chamado.');
    }
  };

  // Filtered tickets list
  const filteredTickets = tickets.filter(t => {
    if (statusFilter && t.status !== statusFilter) return false;
    if (priorityFilter && t.prioridade !== priorityFilter) return false;
    return true;
  });

  return (
    <div className="flex h-full min-h-[calc(100vh-4rem)] bg-brand-dark overflow-hidden">
      {/* Main Panel */}
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-brand-text">Central de Suporte & Chamados</h1>
            <p className="text-sm text-brand-muted">Registre e acompanhe incidentes e solicitações de TI</p>
          </div>
          <div className="flex items-center space-x-3">
            {isTechnicianOrAbove && (
              <button
                onClick={() => setShowConfigModal(true)}
                className="flex items-center space-x-2 px-4 py-2.5 bg-brand-dark border border-brand-border hover:bg-brand-card text-brand-text font-medium transition-all"
              >
                <Plus size={18} />
                <span>Configurar Serviços</span>
              </button>
            )}
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center space-x-2 px-4 py-2.5 bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-medium transition-all"
            >
              <Plus size={18} />
              <span>Abrir Chamado</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="flex items-start space-x-3 p-4 border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
            <AlertCircle size={18} className="shrink-0 mt-0.5" />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto font-bold">×</button>
          </div>
        )}

        {/* Filters */}
        <div className="p-4 bg-brand-card border border-brand-border flex flex-wrap gap-4 items-center">
          <div className="flex items-center space-x-2 text-brand-muted text-sm mr-2">
            <Filter size={16} />
            <span>Filtros:</span>
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-brand-dark border border-brand-border px-3 py-1.5 text-xs text-brand-text focus:outline-none focus:border-brand-primary"
          >
            <option value="">Todos os Status</option>
            <option value="aberto">Aberto</option>
            <option value="em_atendimento">Em Atendimento</option>
            <option value="resolvido">Resolvido</option>
            <option value="fechado">Fechado</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-brand-dark border border-brand-border px-3 py-1.5 text-xs text-brand-text focus:outline-none focus:border-brand-primary"
          >
            <option value="">Todas as Prioridades</option>
            <option value="baixa">Baixa</option>
            <option value="media">Média</option>
            <option value="alta">Alta</option>
            <option value="urgente">Urgente</option>
          </select>
        </div>

        {/* Tickets Grid / List */}
        {loading ? (
          <div className="p-12 text-center text-brand-muted font-mono text-sm">Carregando chamados...</div>
        ) : filteredTickets.length === 0 ? (
          <div className="p-12 border border-brand-border bg-brand-card/20 text-center text-brand-muted text-sm">
            Nenhum chamado encontrado para os filtros selecionados.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {filteredTickets.map((ticket) => (
              <div
                key={ticket.id}
                onClick={() => handleSelectTicket(ticket)}
                className={`p-4 bg-brand-card border transition-all duration-150 cursor-pointer flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 hover:border-brand-primary/40 ${
                  selectedTicket?.id === ticket.id ? 'border-brand-primary bg-brand-primary/5' : 'border-brand-border'
                }`}
              >
                <div className="space-y-2 flex-1 pr-4">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono font-bold text-brand-primary px-1.5 py-0.5 bg-brand-primary/10 border border-brand-primary/20">
                      {ticket.codigo}
                    </span>
                    <span className="text-sm font-semibold text-brand-text">{ticket.titulo}</span>
                  </div>
                  <p className="text-xs text-brand-muted line-clamp-2">{ticket.descricao}</p>
                  <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-brand-muted">
                    <span className="flex items-center space-x-1">
                      <UserIcon size={12} />
                      <span>{ticket.solicitante?.nome || 'Usuário'}</span>
                    </span>
                    <span>•</span>
                    <span className="flex items-center space-x-1">
                      <Clock size={12} />
                      <span>{new Date(ticket.data_abertura).toLocaleDateString('pt-BR')}</span>
                    </span>
                    {ticket.servico?.categoria && (
                      <>
                        <span>•</span>
                        <span className="px-1.5 py-0.2 bg-brand-dark border border-brand-border text-brand-muted">
                          {ticket.servico.categoria.nome}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  {/* Priority Badge */}
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 border ${
                    ticket.prioridade === 'urgente' 
                      ? 'text-red-500 bg-red-500/10 border-red-500/20' 
                      : ticket.prioridade === 'alta' 
                      ? 'text-amber-500 bg-amber-500/10 border-amber-500/20'
                      : ticket.prioridade === 'media'
                      ? 'text-blue-500 bg-blue-500/10 border-blue-500/20'
                      : 'text-brand-muted bg-brand-muted/10 border-brand-border'
                  }`}>
                    {ticket.prioridade}
                  </span>

                  {/* Status Badge */}
                  <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 ${
                    ticket.status === 'aberto'
                      ? 'text-blue-400 bg-blue-400/10 border border-blue-400/20'
                      : ticket.status === 'em_atendimento'
                      ? 'text-amber-400 bg-amber-400/10 border border-amber-400/20'
                      : ticket.status === 'resolvido'
                      ? 'text-brand-primary bg-brand-primary/10 border border-brand-primary/20'
                      : 'text-brand-muted bg-brand-dark border border-brand-border'
                  }`}>
                    {ticket.status.replace('_', ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Slide-out Ticket details panel (Layout Diversification) */}
      {selectedTicket && (
        <div className="w-96 bg-brand-card border-l border-brand-border flex flex-col h-full shrink-0">
          <div className="p-4 border-b border-brand-border flex items-center justify-between bg-brand-dark/30">
            <div>
              <h3 className="font-bold text-brand-text text-sm">{selectedTicket.codigo}</h3>
              <p className="text-[11px] text-brand-muted">Aberto em {new Date(selectedTicket.data_abertura).toLocaleString('pt-BR')}</p>
            </div>
            <button
              onClick={() => setSelectedTicket(null)}
              className="text-brand-muted hover:text-brand-text transition-colors p-1"
            >
              <X size={18} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* Ticket Info */}
            <div className="space-y-3">
              <h4 className="font-semibold text-brand-text text-sm">{selectedTicket.titulo}</h4>
              <p className="text-xs text-brand-muted bg-brand-dark p-3 border border-brand-border/60 rounded-sm whitespace-pre-wrap">
                {selectedTicket.descricao}
              </p>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono border-t border-brand-border/40 pt-3">
                <div className="text-brand-muted">Solicitante:</div>
                <div className="text-brand-text text-right truncate">{selectedTicket.solicitante?.nome}</div>
                
                <div className="text-brand-muted">Serviço:</div>
                <div className="text-brand-text text-right truncate">{selectedTicket.servico?.nome}</div>

                <div className="text-brand-muted">Técnico:</div>
                <div className="text-brand-text text-right truncate">
                  {selectedTicket.tecnico?.nome || selectedTicket.responsavel?.nome || 'Não atribuído'}
                </div>
              </div>
            </div>

            {/* Admin/Technician Management controls */}
            {isTechnicianOrAbove && selectedTicket.status !== 'fechado' && (
              <div className="border-t border-brand-border/60 pt-4 space-y-3">
                <h5 className="text-xs font-semibold text-brand-primary uppercase tracking-wider font-mono">Gerenciamento Técnico</h5>

                {/* Delegation selection */}
                <div className="space-y-1">
                  <label className="text-[10px] text-brand-muted">Delegar para Técnico:</label>
                  <select
                    value={assignedTechId}
                    onChange={(e) => {
                      const id = e.target.value === '' ? '' : Number(e.target.value);
                      setAssignedTechId(id);
                      if (id) handleAssignTicket(id);
                    }}
                    className="w-full bg-brand-dark border border-brand-border px-2 py-1 text-xs text-brand-text focus:outline-none focus:border-brand-primary"
                  >
                    <option value="">Atribuir a...</option>
                    {technicians.map(t => (
                      <option key={t.id} value={t.id}>{t.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="flex space-x-2">
                  {selectedTicket.status !== 'resolvido' && (
                    <button
                      onClick={() => setShowResolutionForm(true)}
                      className="flex-1 py-1.5 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark text-xs font-semibold flex items-center justify-center space-x-1"
                    >
                      <Check size={14} />
                      <span>Resolver Chamado</span>
                    </button>
                  )}
                  {selectedTicket.status === 'resolvido' && (
                    <button
                      onClick={() => handleUpdateStatus('fechado')}
                      className="flex-1 py-1.5 bg-brand-muted/10 border border-brand-border hover:bg-brand-card text-brand-text text-xs font-semibold flex items-center justify-center space-x-1"
                    >
                      <CheckCircle2 size={14} />
                      <span>Fechar Chamado</span>
                    </button>
                  )}
                </div>
              </div>
            )}

            {/* User Rating / Feedback controls */}
            {currentUser?.id === selectedTicket.solicitante_id && 
             selectedTicket.status?.toLowerCase() === 'resolvido' && 
             !selectedTicket.nota_feedback && 
             !selectedTicket.avaliacao && (
              <div className="border-t border-brand-border/60 pt-4 bg-brand-primary/5 p-3 border border-brand-primary/20 space-y-3">
                <h5 className="text-xs font-semibold text-brand-primary flex items-center space-x-1">
                  <Star size={14} />
                  <span>Avaliar Atendimento</span>
                </h5>
                <p className="text-[11px] text-brand-text">Este chamado foi resolvido. Por favor, forneça sua avaliação de atendimento.</p>
                <button
                  onClick={() => setShowFeedbackForm(true)}
                  className="w-full py-1.5 bg-brand-primary text-brand-dark text-xs font-semibold flex items-center justify-center space-x-1"
                >
                  <span>Avaliar e Encerrar</span>
                </button>
              </div>
            )}

            {/* Feedback Detail (if rated) */}
            {(selectedTicket.nota_feedback || selectedTicket.avaliacao) && (
              <div className="border-t border-brand-border/60 pt-4 space-y-2">
                <h5 className="text-xs font-semibold text-brand-text flex items-center space-x-1">
                  <Star size={14} className="text-amber-500" />
                  <span>Avaliação do Usuário</span>
                </h5>
                <div className="flex items-center space-x-1">
                  {[1, 2, 3, 4, 5].map((s) => {
                    const ratingScore = selectedTicket.nota_feedback || selectedTicket.avaliacao || 0;
                    return (
                      <Star
                        key={s}
                        size={14}
                        className={s <= ratingScore ? 'text-amber-500 fill-amber-500' : 'text-brand-muted'}
                      />
                    );
                  })}
                </div>
                {(selectedTicket.comentario_feedback || selectedTicket.feedback_usuario) && (
                  <p className="text-xs italic text-brand-muted font-serif">
                    "{selectedTicket.comentario_feedback || selectedTicket.feedback_usuario}"
                  </p>
                )}
              </div>
            )}

            {/* Resolution Note */}
            {(selectedTicket.nota_resolucao || selectedTicket.solucao) && (
              <div className="border-t border-brand-border/60 pt-4 space-y-1">
                <h5 className="text-xs font-semibold text-brand-text">Solução / Resolução:</h5>
                <p className="text-xs text-brand-muted bg-brand-dark p-2 border border-brand-border/40 font-mono">
                  {selectedTicket.nota_resolucao || selectedTicket.solucao}
                </p>
              </div>
            )}

            {/* Interaction Thread */}
            <div className="border-t border-brand-border/60 pt-4 space-y-3">
              <h5 className="text-xs font-semibold text-brand-text flex items-center space-x-1">
                <MessageSquare size={14} />
                <span>Interações e Comentários</span>
              </h5>
              
              <div className="space-y-3">
                {selectedTicket.interacoes && selectedTicket.interacoes.map((item) => (
                  <div key={item.id} className="text-xs p-2.5 bg-brand-dark/40 border border-brand-border/50">
                    <div className="flex items-center justify-between text-[10px] text-brand-muted mb-1 font-mono">
                      <span className="font-semibold text-brand-text">{item.user?.nome}</span>
                      <span>{new Date(item.data_criacao).toLocaleString('pt-BR')}</span>
                    </div>
                    <p className="text-brand-text text-[11px] whitespace-pre-wrap">{item.mensagem}</p>
                  </div>
                ))}

                {(!selectedTicket.interacoes || selectedTicket.interacoes.length === 0) && (
                  <p className="text-[11px] text-brand-muted text-center py-4">Sem interações registradas.</p>
                )}
              </div>
            </div>
          </div>

          {/* Comment Message Box */}
          {selectedTicket.status !== 'fechado' && (
            <form onSubmit={handleSendComment} className="p-3 border-t border-brand-border bg-brand-dark/20 flex space-x-2">
              <input
                type="text"
                placeholder="Escreva uma mensagem..."
                value={commentMessage}
                onChange={(e) => setCommentMessage(e.target.value)}
                className="flex-1 bg-brand-dark border border-brand-border px-3 py-1.5 text-xs focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/40"
              />
              <button
                type="submit"
                disabled={!commentMessage.trim()}
                className="p-1.5 bg-brand-primary/10 border border-brand-primary/30 text-brand-primary hover:bg-brand-primary hover:text-brand-dark transition-all disabled:opacity-40"
              >
                <Send size={14} />
              </button>
            </form>
          )}
        </div>
      )}

      {/* Create Ticket Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-lg bg-brand-card border border-brand-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border bg-brand-dark/50">
              <h3 className="font-semibold text-lg text-brand-text">Abrir Novo Chamado de Suporte</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleCreateTicket} className="p-6 space-y-4">
              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Selecione o Serviço / Incidente</label>
                <select
                  required
                  value={selectedDefinitionId}
                  onChange={(e) => setSelectedDefinitionId(e.target.value === '' ? '' : Number(e.target.value))}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                >
                  <option value="">Escolha um serviço...</option>
                  {categories.map(cat => (
                    <optgroup key={cat.id} label={cat.nome} className="bg-brand-card text-brand-muted">
                      {definitions
                        .filter(def => def.categoria_id === cat.id)
                        .map(def => (
                          <option key={def.id} value={def.id} className="text-brand-text">{def.nome}</option>
                        ))}
                    </optgroup>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Título Resumido</label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Monitor piscando ou sem imagem"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Descrição Detalhada do Problema</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Explique detalhadamente o ocorrido..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Prioridade Estimada</label>
                <select
                  value={newPriority}
                  onChange={(e: any) => setNewPriority(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary"
                >
                  <option value="baixa">Baixa</option>
                  <option value="media">Média</option>
                  <option value="alta">Alta</option>
                  <option value="urgente">Urgente</option>
                </select>
              </div>

              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="w-1/3 py-2 bg-brand-dark border border-brand-border hover:bg-brand-card text-brand-muted text-sm transition-all"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="flex-1 py-2 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark font-semibold text-sm transition-all"
                >
                  Enviar Chamado
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Resolution Notes Modal */}
      {showResolutionForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-md bg-brand-card border border-brand-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border">
              <h3 className="font-semibold text-brand-text text-sm">Registrar Solução / Resolução</h3>
              <button onClick={() => setShowResolutionForm(false)} className="text-brand-muted hover:text-brand-text">
                <X size={18} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs text-brand-muted">Notas da Resolução Técnico</label>
                <textarea
                  required
                  rows={4}
                  placeholder="Informe o procedimento técnico executado para a resolução do chamado..."
                  value={resolutionNotes}
                  onChange={(e) => setResolutionNotes(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-xs focus:outline-none focus:border-brand-primary text-brand-text"
                />
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowResolutionForm(false)}
                  className="w-1/3 py-1.5 bg-brand-dark border border-brand-border text-xs text-brand-muted"
                >
                  Cancelar
                </button>
                <button
                  onClick={() => handleUpdateStatus('resolvido', resolutionNotes)}
                  disabled={!resolutionNotes.trim()}
                  className="flex-1 py-1.5 bg-brand-primary text-brand-dark text-xs font-semibold disabled:opacity-50"
                >
                  Confirmar Resolução
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* User Feedback Modal */}
      {showFeedbackForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-md bg-brand-card border border-brand-border shadow-2xl overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border">
              <h3 className="font-semibold text-brand-text text-sm">Avaliar e Encerrar Chamado</h3>
              <button onClick={() => setShowFeedbackForm(false)} className="text-brand-muted hover:text-brand-text">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleSendFeedback} className="p-6 space-y-4">
              <div className="space-y-2 text-center">
                <label className="text-xs text-brand-muted">Sua Nota para este Atendimento:</label>
                <div className="flex justify-center space-x-2 pt-2">
                  {[1, 2, 3, 4, 5].map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => setRating(s)}
                      className="p-1 hover:scale-115 transition-transform"
                    >
                      <Star
                        size={28}
                        className={s <= rating ? 'text-amber-500 fill-amber-500' : 'text-brand-muted'}
                      />
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-brand-muted">Comentário Adicional (Opcional)</label>
                <textarea
                  rows={3}
                  placeholder="Escreva sua opinião..."
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-xs focus:outline-none focus:border-brand-primary text-brand-text"
                />
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setShowFeedbackForm(false)}
                  className="w-1/3 py-1.5 bg-brand-dark border border-brand-border text-xs text-brand-muted"
                >
                  Voltar
                </button>
                <button
                  type="submit"
                  className="flex-1 py-1.5 bg-brand-primary text-brand-dark text-xs font-semibold"
                >
                  Enviar e Fechar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    {/* Configuration Modal */}
      {showConfigModal && isTechnicianOrAbove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
          <div className="w-full max-w-2xl bg-brand-card border border-brand-border shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border bg-brand-dark/50">
              <h3 className="font-semibold text-lg text-brand-text">Configurações do Service Desk</h3>
              <button onClick={() => setShowConfigModal(false)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            <div className="flex border-b border-brand-border bg-brand-dark/30">
              <button
                onClick={() => setActiveConfigTab('categorias')}
                className={`flex-1 py-3 text-sm font-semibold transition-colors ${activeConfigTab === 'categorias' ? 'text-brand-primary border-b-2 border-brand-primary' : 'text-brand-muted hover:text-brand-text'}`}
              >
                1. Categorias de Serviço
              </button>
              <button
                onClick={() => setActiveConfigTab('servicos')}
                className={`flex-1 py-3 text-sm font-semibold transition-colors ${activeConfigTab === 'servicos' ? 'text-brand-primary border-b-2 border-brand-primary' : 'text-brand-muted hover:text-brand-text'}`}
              >
                2. Serviços Específicos
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {activeConfigTab === 'categorias' && (
                <div className="space-y-6">
                  <form onSubmit={handleCreateCategory} className="space-y-4 p-4 border border-brand-primary/30 bg-brand-primary/5">
                    <h4 className="text-sm font-bold text-brand-text uppercase font-mono tracking-wider">Nova Categoria</h4>
                    <div className="space-y-1">
                      <label className="text-xs text-brand-muted">Nome da Categoria</label>
                      <input
                        type="text"
                        required
                        value={newCategoryName}
                        onChange={(e) => setNewCategoryName(e.target.value)}
                        placeholder="Ex: Hardware, Redes, Softwares..."
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-brand-muted">Descrição (Opcional)</label>
                      <input
                        type="text"
                        value={newCategoryDesc}
                        onChange={(e) => setNewCategoryDesc(e.target.value)}
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                      />
                    </div>
                    <div className="flex justify-end">
                      <button type="submit" className="px-4 py-2 bg-brand-primary text-brand-dark font-semibold text-xs">
                        Adicionar Categoria
                      </button>
                    </div>
                  </form>

                  <div>
                    <h4 className="text-sm font-bold text-brand-text mb-3">Categorias Existentes</h4>
                    <div className="space-y-2">
                      {categories.map(cat => (
                        <div key={cat.id} className="p-3 bg-brand-dark border border-brand-border flex flex-col text-sm">
                          <span className="font-semibold text-brand-text">{cat.nome}</span>
                          {cat.descricao && <span className="text-xs text-brand-muted">{cat.descricao}</span>}
                        </div>
                      ))}
                      {categories.length === 0 && <p className="text-xs text-brand-muted">Nenhuma categoria cadastrada.</p>}
                    </div>
                  </div>
                </div>
              )}

              {activeConfigTab === 'servicos' && (
                <div className="space-y-6">
                  <form onSubmit={handleCreateDefinition} className="space-y-4 p-4 border border-brand-primary/30 bg-brand-primary/5">
                    <h4 className="text-sm font-bold text-brand-text uppercase font-mono tracking-wider">Novo Serviço/Incidente</h4>
                    
                    <div className="space-y-1">
                      <label className="text-xs text-brand-muted">Categoria Relacionada</label>
                      <select
                        required
                        value={newDefCategoryId}
                        onChange={(e) => setNewDefCategoryId(e.target.value === '' ? '' : Number(e.target.value))}
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text"
                      >
                        <option value="">Selecione uma categoria...</option>
                        {categories.map(cat => (
                          <option key={cat.id} value={cat.id}>{cat.nome}</option>
                        ))}
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-xs text-brand-muted">Nome do Serviço</label>
                      <input
                        type="text"
                        required
                        value={newDefName}
                        onChange={(e) => setNewDefName(e.target.value)}
                        placeholder="Ex: Formatação de Computador"
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                      />
                    </div>
                    <div className="space-y-1">
                      <label className="text-xs text-brand-muted">Descrição / Orientações (Opcional)</label>
                      <textarea
                        rows={2}
                        value={newDefDesc}
                        onChange={(e) => setNewDefDesc(e.target.value)}
                        className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm focus:outline-none focus:border-brand-primary text-brand-text placeholder-brand-muted/30"
                      />
                    </div>
                    <div className="flex justify-end">
                      <button type="submit" className="px-4 py-2 bg-brand-primary text-brand-dark font-semibold text-xs">
                        Adicionar Serviço
                      </button>
                    </div>
                  </form>

                  <div>
                    <h4 className="text-sm font-bold text-brand-text mb-3">Serviços Existentes</h4>
                    <div className="space-y-2">
                      {definitions.map(def => (
                        <div key={def.id} className="p-3 bg-brand-dark border border-brand-border flex flex-col text-sm">
                          <div className="flex justify-between items-start">
                            <span className="font-semibold text-brand-text">{def.nome}</span>
                            <span className="text-[10px] uppercase px-1.5 py-0.5 bg-brand-muted/10 border border-brand-border text-brand-muted">
                              {categories.find(c => c.id === def.categoria_id)?.nome || 'Sem Categoria'}
                            </span>
                          </div>
                          {def.descricao && <span className="text-xs text-brand-muted mt-1">{def.descricao}</span>}
                        </div>
                      ))}
                      {definitions.length === 0 && <p className="text-xs text-brand-muted">Nenhum serviço cadastrado.</p>}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
