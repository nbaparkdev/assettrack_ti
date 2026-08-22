import React, { useState, useEffect } from 'react';
import { usersApi } from '../api/users';
import type { User, UserRole } from '../types';
import { useAuthStore } from '../stores/authStore';
import { Plus, Edit2, Trash2, ShieldAlert, Check, X } from 'lucide-react';

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

  const [formError, setFormError] = useState<string | null>(null);

  const [setores, setSetores] = useState<any[]>([]);

  const fetchUsersAndRefs = async () => {
    setLoading(true);
    try {
      const [usersData, refsData] = await Promise.all([
        usersApi.list(0, 100),
        import('../api/assets').then(m => m.assetsApi.getReferences())
      ]);
      setUsers(usersData);
      setSetores(refsData.setores || []);
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
    </div>
  );
};
