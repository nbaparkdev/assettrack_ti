import React, { useState, useEffect } from 'react';
import { rhApi } from '../api/rh';
import { apiClient as api } from '../api/client';
import type { TermoResponsabilidade } from '../types/rh';
import type { Solicitacao } from '../types/transaction';
import type { User } from '../types/user';
import { FileSignature, Printer, CheckCircle2, XCircle, Edit2, Plus, UserMinus } from 'lucide-react';
import jsPDF from 'jspdf';

const statusStyles: Record<string, string> = {
  Pendente: 'border-yellow-500/30 text-yellow-400',
  Assinado: 'border-green-500/30 text-green-400',
  Cancelado: 'border-red-500/30 text-red-400',
};

export const RHPage: React.FC = () => {
  const [termos, setTermos] = useState<TermoResponsabilidade[]>([]);
  const [pendentes, setPendentes] = useState<Solicitacao[]>([]);
  const [usuarios, setUsuarios] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal de criação/edição
  const [modal, setModal] = useState(false);
  const [editing, setEditing] = useState<TermoResponsabilidade | null>(null);
  const [solId, setSolId] = useState<number | null>(null);
  const [conteudo, setConteudo] = useState('');
  const [saving, setSaving] = useState(false);

  const fetchData = async () => {
    try {
      const data = await rhApi.list();
      setTermos(data.termos ?? []);
      setPendentes(data.pendentes ?? []);

      // Load active users
      const res = await api.get<User[]>('/users');
      setUsuarios((res.data || []).filter(u => {
        // Must be active in the system
        if (!u.is_active) return false;
        
        // Must NOT be an administrator
        if (u.role === 'admin') return false;
        
        // Allowed roles: comum, rh, compras, gerentes, tecnico
        const allowedRoles = ['usuario_comum', 'rh', 'comprador', 'gerente_ti', 'gerente_infra', 'tecnico'];
        if (!allowedRoles.includes(u.role)) return false;
        
        return true;
      }));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openCreate = async (solicitacao: Solicitacao) => {
    setEditing(null);
    setSolId(solicitacao.id);
    try {
      const tpl = await rhApi.generateTemplate(solicitacao.id);
      setConteudo(tpl.conteudo_termo);
    } catch {
      setConteudo('');
    }
    setModal(true);
  };

  const openEdit = (termo: TermoResponsabilidade) => {
    setEditing(termo);
    setSolId(null);
    setConteudo(termo.conteudo_termo);
    setModal(true);
  };

  const save = async () => {
    if (!conteudo.trim()) return;
    setSaving(true);
    try {
      if (editing) {
        await rhApi.update(editing.id, conteudo);
      } else {
        await rhApi.create({ solicitacao_id: solId ?? undefined, conteudo_termo: conteudo });
      }
      setModal(false);
      await fetchData();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const generatePdfFrontend = (termo: TermoResponsabilidade) => {
    try {
      const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(16);
      doc.text('Termo de Responsabilidade', 105, 20, { align: 'center' });

      doc.setFont('courier', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(100, 100, 100);
      doc.text('NBAPARK // CONTROLE INTERNO DE ATIVOS DE TI', 105, 26, { align: 'center' });

      doc.setDrawColor(0);
      doc.setLineWidth(0.5);
      doc.line(20, 30, 190, 30);

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(11);
      doc.setTextColor(17, 17, 17);

      const splitText = doc.splitTextToSize(termo.conteudo_termo, 170);
      doc.text(splitText, 20, 40);

      doc.setFont('courier', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(120, 120, 120);
      doc.setDrawColor(200);
      doc.line(20, 270, 190, 270);
      const dateStr = new Date().toLocaleString('pt-BR');
      const nome = termo.usuario?.nome || '-';
      const pat = termo.asset?.e_patrimonio || '-';
      doc.text(`Documento gerado eletronicamente em ${dateStr} pelo módulo RH Audit Workflow.`, 20, 275);
      doc.text(`Identificador do Termo: #${termo.id} · Ref: Patrimônio ${pat}`, 20, 280);

      doc.save(`termo_${termo.id}_${nome.replace(/\\s+/g, '_')}.pdf`);
    } catch (err) {
      console.error(err);
      alert('Erro ao gerar PDF no navegador.');
    }
  };

  const action = async (fn: () => Promise<unknown>, confirmMsg?: string) => {
    if (confirmMsg && !window.confirm(confirmMsg)) return;
    try {
      await fn();
      await fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="text-brand-muted font-mono text-sm">Carregando...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">Portal RH</h1>
        <p className="text-brand-muted text-sm mt-1">
          Termos de Responsabilidade pela guarda e uso de equipamentos.
        </p>
      </div>

      {/* Solicitações pendentes de termo */}
      <div className="border border-brand-border bg-brand-card">
        <div className="p-4 border-b border-brand-border text-sm font-bold font-mono uppercase tracking-wider text-brand-text flex items-center">
          <FileSignature size={16} className="mr-2 text-yellow-400" /> Solicitações pendentes de termo
        </div>
        <div className="divide-y divide-brand-border/60">
          {pendentes.map((s) => (
            <div key={s.id} className="p-4 flex justify-between items-center gap-4">
              <div className="min-w-0">
                <span className="font-mono text-xs text-brand-primary">
                  #{s.id} — {s.solicitante?.nome ?? '—'}
                </span>
                <p className="text-sm text-brand-text mt-1 m-0">
                  {s.asset?.nome ?? '—'}{' '}
                  <span className="text-brand-muted font-mono text-xs">({s.asset?.e_patrimonio ?? 'sem patrimônio'})</span>
                </p>
                <span className="text-xs font-mono text-brand-muted">
                  {s.status} · {new Date(s.data_solicitacao).toLocaleDateString('pt-BR')}
                </span>
              </div>
              <button
                onClick={() => openCreate(s)}
                className="shrink-0 bg-brand-primary text-brand-dark font-bold font-mono px-3 py-2 uppercase tracking-wider text-xs flex items-center space-x-1.5"
              >
                <Plus size={14} />
                <span>Gerar Termo</span>
              </button>
            </div>
          ))}
          {pendentes.length === 0 && (
            <div className="p-6 text-center text-brand-muted font-mono text-xs">
              Nenhuma solicitação pendente de termo.
            </div>
          )}
        </div>
      </div>

      {/* Termos */}
      <div className="border border-brand-border bg-brand-card">
        <div className="p-4 border-b border-brand-border text-sm font-bold font-mono uppercase tracking-wider text-brand-text">
          Termos de Responsabilidade
        </div>
        <div className="divide-y divide-brand-border/60">
          {termos.map((t) => (
            <div key={t.id} className="p-4">
              <div className="flex justify-between items-start gap-4">
                <div className="min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-brand-text">
                      {t.usuario?.nome ?? '—'} — {t.asset?.nome ?? '—'}
                    </span>
                    <span className={`text-[10px] font-mono uppercase px-1.5 py-0.5 border ${statusStyles[t.status] ?? 'border-brand-border text-brand-muted'}`}>
                      {t.status}
                    </span>
                  </div>
                  <span className="text-xs font-mono text-brand-muted">
                    Termo #{t.id} · criado em {new Date(t.data_criacao).toLocaleDateString('pt-BR')}
                    {t.data_assinatura ? ` · assinado em ${new Date(t.data_assinatura).toLocaleDateString('pt-BR')}` : ''}
                  </span>
                </div>
                <div className="flex space-x-2 shrink-0">
                  <button
                    onClick={() => generatePdfFrontend(t)}
                    title="Imprimir / Gerar PDF"
                    className="text-brand-primary border border-brand-primary/30 px-2 py-1.5"
                  >
                    <Printer size={14} />
                  </button>
                  {t.status === 'Pendente' && (
                    <>
                      <button
                        onClick={() => openEdit(t)}
                        title="Editar conteúdo"
                        className="text-brand-muted border border-brand-border px-2 py-1.5 hover:text-brand-text"
                      >
                        <Edit2 size={14} />
                      </button>
                      <button
                        onClick={() => action(() => rhApi.sign(t.id), `Assinar o termo #${t.id}?`)}
                        title="Assinar"
                        className="text-green-400 border border-green-500/30 px-2 py-1.5"
                      >
                        <CheckCircle2 size={14} />
                      </button>
                    </>
                  )}
                  {t.status !== 'Cancelado' && (
                    <button
                      onClick={() => action(() => rhApi.cancel(t.id), `Cancelar o termo #${t.id}?`)}
                      title="Cancelar"
                      className="text-red-400 border border-red-500/30 px-2 py-1.5"
                    >
                      <XCircle size={14} />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
          {termos.length === 0 && (
            <div className="p-6 text-center text-brand-muted font-mono text-xs">Nenhum termo cadastrado.</div>
          )}
        </div>
      </div>

      {/* Desligamento de Colaborador */}
      <div className="border border-brand-border bg-brand-card">
        <div className="p-4 border-b border-brand-border text-sm font-bold font-mono uppercase tracking-wider text-red-500 flex items-center">
          <UserMinus size={16} className="mr-2" /> Desligamento de Colaborador (Offboarding)
        </div>
        <div className="p-4 bg-brand-dark/50 border-b border-brand-border text-xs text-brand-muted font-mono leading-relaxed">
          Ao desligar um colaborador, o acesso ao sistema será imediatamente revogado. Um <strong>alerta emergencial</strong> será disparado automaticamente para a equipe técnica e administradores, informando os ativos em posse do usuário para que realizem a <strong>solicitação de devolução</strong> utilizando o fluxo padrão de Empréstimos/Inventário.
        </div>
        <div className="divide-y divide-brand-border/60 max-h-[300px] overflow-y-auto">
          {usuarios.map((u) => (
            <div key={u.id} className="p-4 flex justify-between items-center gap-4">
              <div className="min-w-0">
                <span className="font-bold text-brand-text block">{u.nome}</span>
                <span className="font-mono text-xs text-brand-muted block mt-0.5">
                  Matrícula: {u.matricula || 'N/A'} · Cargo: {u.cargo || 'N/A'} · Email: {u.email}
                </span>
              </div>
              <button
                onClick={() => action(() => rhApi.offboardUser(u.id), `Tem certeza que deseja processar o DESLIGAMENTO de ${u.nome}? Os acessos serão revogados e os ativos recolhidos.`)}
                className="shrink-0 text-red-500 border border-red-500/30 font-bold font-mono px-3 py-2 uppercase tracking-wider text-xs hover:bg-red-500/10"
              >
                Desligar
              </button>
            </div>
          ))}
          {usuarios.length === 0 && (
            <div className="p-6 text-center text-brand-muted font-mono text-xs">Nenhum colaborador ativo encontrado.</div>
          )}
        </div>
      </div>

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-brand-card border border-brand-border w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="p-4 border-b border-brand-border flex justify-between items-center">
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-brand-text m-0">
                {editing ? `Editar Termo #${editing.id}` : 'Novo Termo de Responsabilidade'}
              </h3>
              <button onClick={() => setModal(false)} className="text-brand-muted hover:text-brand-text font-mono">
                Fechar
              </button>
            </div>
            <div className="p-4 flex-1 overflow-y-auto">
              <textarea
                value={conteudo}
                onChange={(e) => setConteudo(e.target.value)}
                rows={18}
                className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary/50 font-mono"
              />
            </div>
            <div className="p-4 border-t border-brand-border flex justify-end space-x-3">
              <button
                onClick={() => setModal(false)}
                className="border border-brand-border text-brand-muted px-4 py-2.5 font-mono uppercase tracking-wider text-xs hover:text-brand-text"
              >
                Cancelar
              </button>
              <button
                onClick={save}
                disabled={saving || !conteudo.trim()}
                className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs disabled:opacity-50"
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
