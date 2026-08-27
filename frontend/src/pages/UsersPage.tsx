import React, { useState, useEffect } from 'react';
import { usersApi } from '../api/users';
import { toApiFileUrl } from '../api/client';
import type { User, UserRole, UserHistoryReport } from '../types';
import { useAuthStore } from '../stores/authStore';
import { Plus, Edit2, Trash2, ShieldAlert, Check, X, FileText, Download, Loader2 } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const imageUrlToDataUrl = async (url: string): Promise<string | null> => {
  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    const blob = await response.blob();
    return await new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(typeof reader.result === 'string' ? reader.result : null);
      reader.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
};

export const UsersPage: React.FC = () => {
  const currentAuthUser = useAuthStore().user;
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);

  // Form State
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [matricula, setMatricula] = useState('');
  const [cargo, setCargo] = useState('');
  const [role, setRole] = useState<UserRole>('usuario_comum');
  const [isActive, setIsActive] = useState(true);
  const [departamentoId, setDepartamentoId] = useState<number | null>(null);
  const [localizacaoId, setLocalizacaoId] = useState<number | null>(null);

  const [formError, setFormError] = useState<string | null>(null);

  const [setores, setSetores] = useState<any[]>([]);
  const [localizacoes, setLocalizacoes] = useState<any[]>([]);
  const [historyReport, setHistoryReport] = useState<UserHistoryReport | null>(null);
  const [historyLoading, setHistoryLoading] = useState<number | null>(null);
  const [historyPdfLoading, setHistoryPdfLoading] = useState(false);

  const fetchUsersAndRefs = async () => {
    setLoading(true);
    try {
      const [usersData, refsData] = await Promise.all([
        usersApi.list(0, 100),
        import('../api/assets').then(m => m.assetsApi.getReferences())
      ]);
      setUsers(usersData);
      setSetores(refsData.setores || []);
      setLocalizacoes(refsData.localizacoes || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndRefs();
  }, []);

  const openCreateModal = () => {
    setEditId(null);
    setNome('');
    setEmail('');
    setPassword('');
    setMatricula('');
    setCargo('');
    setRole('usuario_comum');
    setIsActive(true);
    setDepartamentoId(null);
    setLocalizacaoId(null);
    setFormError(null);
    setShowModal(true);
  };

  const openEditModal = (u: User) => {
    setEditId(u.id);
    setNome(u.nome);
    setEmail(u.email);
    setPassword(''); // leave blank for no change
    setMatricula(u.matricula || '');
    setCargo(u.cargo || '');
    setRole(u.role);
    setIsActive(u.is_active);
    setDepartamentoId(u.departamento_id);
    setLocalizacaoId(u.localizacao_id);
    setFormError(null);
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const payload: any = {
      nome,
      email,
      role,
      is_active: isActive,
      matricula: matricula || undefined,
      cargo: cargo || undefined,
      departamento_id: departamentoId || undefined,
      localizacao_id: localizacaoId || undefined,
    };

    if (password) {
      payload.password = password;
    }

    try {
      if (editId) {
        await usersApi.update(editId, payload);
      } else {
        if (!password) {
          setFormError('Senha é obrigatória para criação de usuário');
          return;
        }
        await usersApi.create({ ...payload, password });
      }
      setShowModal(false);
      fetchUsersAndRefs();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Erro ao salvar usuário');
    }
  };

  const handleDelete = async (u: User) => {
    if (window.confirm(`Tem certeza que deseja excluir o usuário "${u.nome}"? Esta ação não pode ser desfeita e removerá seus acessos.`)) {
      try {
        await usersApi.delete(u.id);
        fetchUsersAndRefs();
      } catch (err: any) {
        alert(err.response?.data?.detail || 'Erro ao excluir usuário. Verifique se ele possui registros vinculados.');
      }
    }
  };

  const openHistoryReport = async (u: User) => {
    setHistoryLoading(u.id);
    try {
      setHistoryReport(await usersApi.getHistoryReport(u.id));
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Não foi possível carregar o histórico do usuário.');
    } finally {
      setHistoryLoading(null);
    }
  };

  const downloadHistoryPdf = async () => {
    if (!historyReport) return;
    setHistoryPdfLoading(true);
    try {
      const { usuario, resumo, ativos, eventos } = historyReport;
      const doc = new jsPDF();
      doc.setTextColor(23, 43, 77);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(18);
      doc.text('AssetTrack TI — Histórico do Usuário', 14, 18);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.setTextColor(100, 116, 139);
      doc.text(`Gerado em ${new Date().toLocaleString('pt-BR')}`, 14, 25);

      let profileX = 14;
      if (usuario.avatar_url) {
        const avatar = await imageUrlToDataUrl(toApiFileUrl(usuario.avatar_url));
        if (avatar) {
          doc.addImage(avatar, 'JPEG', 14, 32, 28, 28);
          profileX = 48;
        }
      }
      doc.setTextColor(23, 43, 77);
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(14);
      doc.text(usuario.nome, profileX, 39);
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(9);
      doc.text(`E-mail: ${usuario.email}`, profileX, 46);
      doc.text(`Cargo: ${usuario.cargo || 'Não informado'} · Matrícula: ${usuario.matricula || 'N/D'}`, profileX, 52);
      doc.text(`Departamento: ${usuario.departamento?.nome || 'Não informado'}`, profileX, 58);

      if (historyReport.qr_code_base64) {
        doc.addImage(`data:image/png;base64,${historyReport.qr_code_base64}`, 'PNG', 165, 30, 30, 30);
      }

      autoTable(doc, {
        startY: 70,
        theme: 'grid',
        headStyles: { fillColor: [12, 102, 228] },
        head: [['Resumo', 'Quantidade']],
        body: [
          ['Ativos em posse', String(resumo.ativos || 0)],
          ['Tickets relacionados', String(resumo.tickets || 0)],
          ['Solicitações de manutenção', String(resumo.manutencoes || 0)],
          ['Solicitações de ativos', String(resumo.solicitacoes_ativos || 0)],
          ['Movimentações', String(resumo.movimentacoes || 0)],
        ],
      });

      let nextY = (doc as any).lastAutoTable.finalY + 10;
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.text('Ativos atualmente vinculados', 14, nextY);
      autoTable(doc, {
        startY: nextY + 4,
        theme: 'striped',
        headStyles: { fillColor: [56, 189, 248] },
        head: [['Equipamento', 'Patrimônio', 'Status', 'S/N']],
        body: ativos.length ? ativos.map((asset) => [asset.nome, asset.e_patrimonio, asset.status, asset.numero_serie || '—']) : [['Nenhum ativo vinculado', '—', '—', '—']],
      });

      nextY = (doc as any).lastAutoTable.finalY + 10;
      doc.setFont('helvetica', 'bold');
      doc.text('Histórico operacional', 14, nextY);
      autoTable(doc, {
        startY: nextY + 4,
        theme: 'grid',
        styles: { fontSize: 7, cellPadding: 2 },
        headStyles: { fillColor: [23, 43, 77] },
        head: [['Data', 'Categoria / tipo', 'Referência', 'Descrição', 'Status']],
        body: eventos.length ? eventos.map((event) => [
          new Date(event.data).toLocaleString('pt-BR'),
          `${event.categoria} / ${event.tipo}`,
          event.referencia || '—',
          `${event.titulo}${event.ativo ? ` — ${event.ativo}` : ''}`,
          event.status || '—',
        ]) : [['—', '—', 'Nenhum registro', 'Não há histórico operacional.', '—']],
      });

      const pageCount = (doc as any).internal.getNumberOfPages();
      for (let page = 1; page <= pageCount; page += 1) {
        doc.setPage(page);
        doc.setFontSize(8);
        doc.setTextColor(120);
        doc.text(`Página ${page} de ${pageCount} · AssetTrack TI`, 14, doc.internal.pageSize.height - 8);
      }
      doc.save(`historico_${usuario.nome.toLowerCase().replace(/[^a-z0-9]+/gi, '_')}.pdf`);
    } finally {
      setHistoryPdfLoading(false);
    }
  };

  const rolesList: { value: UserRole; label: string }[] = [
    { value: 'admin', label: 'Administrador' },
    { value: 'gerente_ti', label: 'Gerente TI' },
    { value: 'tecnico', label: 'Técnico' },
    { value: 'gerente_infra', label: 'Gerente Infra' },
    { value: 'comprador', label: 'Comprador' },
    { value: 'usuario_comum', label: 'Usuário Comum' },
    { value: 'rh', label: 'Recursos Humanos' },
  ];

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">
            Usuários
          </h1>
          <p className="text-brand-muted text-xs sm:text-sm mt-1">
            Visualização de colaboradores e atribuição de permissões no sistema.
          </p>
        </div>

        {currentAuthUser?.role === 'admin' && (
          <button
            onClick={openCreateModal}
            className="w-full sm:w-auto bg-brand-primary hover:bg-brand-primary/90 text-white font-bold font-mono px-4 py-2.5 rounded-xl uppercase tracking-wider text-xs flex items-center justify-center space-x-1.5 transition-all shadow-md shadow-brand-primary/20 active:scale-95 cursor-pointer min-h-[40px]"
          >
            <Plus size={16} />
            <span>Novo Usuário</span>
          </button>
        )}
      </div>

      {/* Users Table */}
      <div className="border border-brand-border bg-brand-card">
        {loading ? (
          <div className="p-12 text-center flex flex-col items-center justify-center space-y-4">
            <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent animate-spin" />
            <span className="font-mono text-xs text-brand-muted uppercase">Carregando usuários...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">Colaborador</th>
                  <th className="p-4">Matrícula</th>
                  <th className="p-4">Cargo / Depto</th>
                  <th className="p-4">Nível</th>
                  <th className="p-4 text-center">Status</th>
                  {currentAuthUser?.role === 'admin' && <th className="p-4 text-right">Ações</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-brand-dark/10">
                    <td className="p-4">
                      <div className="font-medium text-brand-text">{u.nome}</div>
                      <div className="text-xs text-brand-muted font-mono">{u.email}</div>
                    </td>
                    <td className="p-4 font-mono text-xs">{u.matricula || '—'}</td>
                    <td className="p-4">
                      <div className="text-brand-text">{u.cargo || '—'}</div>
                      <div className="text-xs text-brand-muted">{u.departamento?.nome || '—'}</div>
                    </td>
                    <td className="p-4">
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-brand-border bg-brand-dark/30">
                        {u.role.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="p-4 text-center">
                      <span className={`inline-flex items-center justify-center w-6 h-6 border ${
                        u.is_active
                          ? 'border-brand-primary/30 bg-brand-primary/5 text-brand-primary'
                          : 'border-red-500/30 bg-red-500/5 text-red-400'
                      }`}>
                        {u.is_active ? <Check size={14} /> : <X size={14} />}
                      </span>
                    </td>
                    {currentAuthUser?.role === 'admin' && (
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => openHistoryReport(u)}
                          disabled={historyLoading === u.id}
                          className="text-cyan-600 hover:bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-1.5 font-mono text-xs uppercase disabled:opacity-50"
                          title="Ver histórico completo e gerar PDF"
                        >
                          {historyLoading === u.id ? <Loader2 size={12} className="inline mr-1 animate-spin" /> : <FileText size={12} className="inline mr-1" />}
                          Histórico
                        </button>
                        <button
                          onClick={() => openEditModal(u)}
                          className="text-brand-primary hover:bg-brand-primary/10 border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase"
                        >
                          <Edit2 size={12} className="inline mr-1" />
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(u)}
                          className="text-red-400 hover:bg-red-500/10 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase"
                        >
                          <Trash2 size={12} className="inline mr-1" />
                          Excluir
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg border border-brand-border bg-brand-card p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                {editId ? 'Editar Usuário' : 'Novo Usuário'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-brand-muted hover:text-brand-text"
              >
                <X size={20} />
              </button>
            </div>

            {formError && (
              <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
                <ShieldAlert size={16} />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Nome Completo
                  </label>
                  <input
                    type="text"
                    required
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    E-mail
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Senha {editId && '(deixe em branco para manter)'}
                  </label>
                  <input
                    type="password"
                    required={!editId}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Matrícula
                  </label>
                  <input
                    type="text"
                    value={matricula}
                    onChange={(e) => setMatricula(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Cargo
                  </label>
                  <input
                    type="text"
                    value={cargo}
                    onChange={(e) => setCargo(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Nível de Acesso (Role)
                  </label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as UserRole)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  >
                    {rolesList.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                  Setor (Departamento)
                </label>
                <select
                  value={departamentoId || ''}
                  onChange={(e) => setDepartamentoId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                >
                  <option value="">-- Nenhum --</option>
                  {setores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.nome}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                  Localização atual
                </label>
                <select
                  value={localizacaoId || ''}
                  onChange={(e) => setLocalizacaoId(e.target.value ? Number(e.target.value) : null)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                >
                  <option value="">-- Nenhuma --</option>
                  {localizacoes.map((local) => (
                    <option key={local.id} value={local.id}>{local.nome}</option>
                  ))}
                </select>
                <p className="text-[10px] text-brand-muted mt-1">Será aplicada automaticamente aos ativos em posse deste usuário.</p>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  id="isActive"
                  type="checkbox"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="rounded-none accent-brand-primary border-brand-border"
                />
                <label htmlFor="isActive" className="text-xs font-mono uppercase tracking-wider text-brand-text select-none cursor-pointer">
                  Usuário Ativo no Sistema
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                >
                  Confirmar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {historyReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-brand-dark/80 p-4 backdrop-blur-sm">
          <div className="flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl border border-brand-border bg-brand-card shadow-2xl">
            <div className="flex items-center justify-between border-b border-brand-border px-6 py-4">
              <div>
                <h3 className="text-lg font-bold uppercase tracking-wider text-brand-text">Histórico completo</h3>
                <p className="mt-1 text-xs text-brand-muted">{historyReport.usuario.nome}</p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={downloadHistoryPdf}
                  disabled={historyPdfLoading}
                  className="flex items-center gap-2 rounded-lg bg-brand-primary px-3 py-2 text-xs font-bold uppercase text-white disabled:opacity-60"
                >
                  {historyPdfLoading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                  Baixar PDF
                </button>
                <button type="button" onClick={() => setHistoryReport(null)} className="text-brand-muted hover:text-brand-text" aria-label="Fechar histórico">
                  <X size={20} />
                </button>
              </div>
            </div>

            <div className="overflow-y-auto p-6">
              <div className="grid grid-cols-1 gap-5 rounded-xl border border-brand-border bg-brand-dark/20 p-4 md:grid-cols-[1fr_150px]">
                <div className="flex items-center gap-4">
                  <div className="h-20 w-20 overflow-hidden rounded-xl border border-brand-border bg-brand-dark">
                    {historyReport.usuario.avatar_url ? <img src={toApiFileUrl(historyReport.usuario.avatar_url)} alt={historyReport.usuario.nome} className="h-full w-full object-cover" /> : <div className="grid h-full place-items-center text-xl font-bold text-brand-primary">{historyReport.usuario.nome.slice(0, 2).toUpperCase()}</div>}
                  </div>
                  <div>
                    <h4 className="text-xl font-bold text-brand-text">{historyReport.usuario.nome}</h4>
                    <p className="text-sm text-brand-muted">{historyReport.usuario.email}</p>
                    <p className="mt-1 text-xs uppercase text-brand-primary">{historyReport.usuario.cargo || 'Colaborador'} · {historyReport.usuario.departamento?.nome || 'Sem departamento'}</p>
                  </div>
                </div>
                <div className="flex justify-center rounded-lg bg-white p-2">
                  <img src={`data:image/png;base64,${historyReport.qr_code_base64}`} alt="QR Code do usuário" className="h-32 w-32" />
                </div>
              </div>

              <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-5">
                {[
                  ['Ativos', historyReport.resumo.ativos],
                  ['Tickets', historyReport.resumo.tickets],
                  ['Manutenções', historyReport.resumo.manutencoes],
                  ['Solicitações', historyReport.resumo.solicitacoes_ativos],
                  ['Movimentações', historyReport.resumo.movimentacoes],
                ].map(([label, value]) => <div key={String(label)} className="rounded-lg border border-brand-border bg-brand-dark/20 p-3"><div className="text-xl font-bold text-brand-primary">{value}</div><div className="text-[10px] uppercase text-brand-muted">{label}</div></div>)}
              </div>

              <div className="mt-6 overflow-x-auto rounded-xl border border-brand-border">
                <table className="w-full min-w-[760px] text-left text-xs">
                  <thead className="bg-brand-dark/30 uppercase text-brand-muted"><tr><th className="p-3">Data</th><th className="p-3">Categoria</th><th className="p-3">Referência</th><th className="p-3">Descrição</th><th className="p-3">Status</th></tr></thead>
                  <tbody className="divide-y divide-brand-border/60">{historyReport.eventos.map((event) => <tr key={`${event.categoria}-${event.referencia}-${event.data}`}><td className="p-3 whitespace-nowrap">{new Date(event.data).toLocaleString('pt-BR')}</td><td className="p-3">{event.categoria} · {event.tipo}</td><td className="p-3 font-mono">{event.referencia || '—'}</td><td className="p-3">{event.titulo}{event.ativo ? ` · ${event.ativo}` : ''}</td><td className="p-3">{event.status || '—'}</td></tr>)}{historyReport.eventos.length === 0 && <tr><td colSpan={5} className="p-8 text-center text-brand-muted">Nenhum registro encontrado.</td></tr>}</tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
