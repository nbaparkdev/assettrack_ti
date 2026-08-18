import React, { useState, useEffect } from 'react';
import { assetsApi } from '../api/assets';
import type { Departamento } from '../types';
import { useAuthStore } from '../stores/authStore';
import { Plus, Trash2, ShieldAlert, X } from 'lucide-react';

export const SetoresPage: React.FC = () => {
  const currentAuthUser = useAuthStore().user;
  const [setores, setSetores] = useState<Departamento[]>([]);
  const [loading, setLoading] = useState(false);

  // Form State
  const [showModal, setShowModal] = useState(false);
  const [nome, setNome] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const fetchSetores = async () => {
    setLoading(true);
    try {
      const data = await assetsApi.getReferences();
      setSetores(data.setores || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSetores();
  }, []);

  const openCreateModal = () => {
    setNome('');
    setFormError(null);
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!nome.trim()) {
      setFormError('O nome do setor é obrigatório.');
      return;
    }

    try {
      await assetsApi.createDepartamento(nome.trim());
      setShowModal(false);
      fetchSetores();
    } catch (err: any) {
      setFormError(err.response?.data?.error || 'Erro ao criar setor');
    }
  };

  const handleDelete = async (s: Departamento) => {
    if (window.confirm(`Tem certeza que deseja excluir o setor "${s.nome}"? Esta ação não pode ser desfeita.`)) {
      try {
        await assetsApi.deleteDepartamento(s.id);
        fetchSetores();
      } catch (err: any) {
        alert(err.response?.data?.error || 'Erro ao excluir setor. Verifique se ele possui usuários ou ativos vinculados.');
      }
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">
            Setores (Departamentos)
          </h1>
          <p className="text-brand-muted text-sm mt-1">
            Gerenciamento de setores/departamentos da empresa.
          </p>
        </div>

        {['admin', 'gerente_ti'].includes(currentAuthUser?.role || '') && (
          <button
            onClick={openCreateModal}
            className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5 transition-colors"
          >
            <Plus size={16} />
            <span>Novo Setor</span>
          </button>
        )}
      </div>

      {/* Setores Table */}
      <div className="border border-brand-border bg-brand-card">
        {loading ? (
          <div className="p-12 text-center flex flex-col items-center justify-center space-y-4">
            <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent animate-spin" />
            <span className="font-mono text-xs text-brand-muted uppercase">Carregando setores...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4 w-20 text-center">ID</th>
                  <th className="p-4">Nome do Setor</th>
                  {['admin', 'gerente_ti'].includes(currentAuthUser?.role || '') && <th className="p-4 text-right">Ações</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {setores.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="p-8 text-center text-brand-muted font-mono text-sm">
                      Nenhum setor cadastrado.
                    </td>
                  </tr>
                ) : (
                  setores.map((s) => (
                    <tr key={s.id} className="hover:bg-brand-dark/10">
                      <td className="p-4 font-mono text-xs text-brand-muted text-center">#{s.id}</td>
                      <td className="p-4">
                        <div className="font-medium text-brand-text">{s.nome}</div>
                      </td>
                      {['admin', 'gerente_ti'].includes(currentAuthUser?.role || '') && (
                        <td className="p-4 text-right space-x-2">
                          <button
                            onClick={() => handleDelete(s)}
                            className="text-red-400 hover:bg-red-500/10 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase"
                          >
                            <Trash2 size={12} className="inline mr-1" />
                            Excluir
                          </button>
                        </td>
                      )}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md border border-brand-border bg-brand-card p-6 space-y-6">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                Novo Setor
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
              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                  Nome do Setor
                </label>
                <input
                  type="text"
                  required
                  value={nome}
                  onChange={(e) => setNome(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="border border-brand-border hover:bg-brand-card px-4 py-2 font-mono text-xs uppercase text-brand-muted"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-xs"
                >
                  Salvar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
