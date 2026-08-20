import React, { useState, useEffect } from 'react';
import { suppliersApi } from '../api/suppliers';
import type { Fornecedor, NotaFiscal, XMLParsedSupplier } from '../types/supplier';
import { useAuthStore } from '../stores/authStore';
import { Plus, Edit2, Trash2, FileText, ShieldAlert, X } from 'lucide-react';

const canManage = ['admin', 'gerente_ti', 'gerente_infra', 'comprador'];

const normalizeXMLImportError = (message?: string) => {
  if (!message) return 'Erro ao processar XML';
  if (message.includes('malformado') || message.includes('incompleto')) {
    return `${message} Dica: valide o XML antes de importar e confirme se não há tags abertas/fechadas incorretamente.`;
  }
  if (message.includes('estrutura de NF-e reconhecida') || message.includes('infNFe')) {
    return `${message} Dica: use um XML de NF-e processada ou autorizado, contendo os dados do emitente.`;
  }
  return message;
};

export const SuppliersPage: React.FC = () => {
  const currentAuthUser = useAuthStore().user;
  const manage = currentAuthUser ? canManage.includes(currentAuthUser.role) : false;

  const [suppliers, setSuppliers] = useState<Fornecedor[]>([]);
  const [loading, setLoading] = useState(false);

  // Form state
  const [showModal, setShowModal] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [nome, setNome] = useState('');
  const [razaoSocial, setRazaoSocial] = useState('');
  const [cnpj, setCnpj] = useState('');
  const [telefone, setTelefone] = useState('');
  const [email, setEmail] = useState('');
  const [endereco, setEndereco] = useState('');
  const [cidade, setCidade] = useState('');
  const [estado, setEstado] = useState('');
  const [tipoFornecedor, setTipoFornecedor] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [xmlPreview, setXmlPreview] = useState<XMLParsedSupplier | null>(null);

  // Invoice state
  const [invoiceSupplier, setInvoiceSupplier] = useState<Fornecedor | null>(null);
  const [invoices, setInvoices] = useState<{ id: number; numero_nota: string }[]>([]);
  const [invoiceDetail, setInvoiceDetail] = useState<NotaFiscal | null>(null);
  const [invoiceError, setInvoiceError] = useState<string | null>(null);

  const formatCurrency = (value?: number | null) =>
    value == null ? 'N/A' : value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

  const formatDateTime = (value?: string | null) =>
    value ? new Date(value).toLocaleString('pt-BR') : 'N/A';

  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const data = await suppliersApi.list(0, 100);
      setSuppliers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const openCreateModal = () => {
    setEditId(null);
    setNome('');
    setRazaoSocial('');
    setCnpj('');
    setTelefone('');
    setEmail('');
    setEndereco('');
    setCidade('');
    setEstado('');
    setTipoFornecedor('');
    setFormError(null);
    setXmlPreview(null);
    setShowModal(true);
  };

  const openEditModal = (s: Fornecedor) => {
    setEditId(s.id);
    setNome(s.nome);
    setRazaoSocial(s.razao_social || '');
    setCnpj(s.cnpj || '');
    setTelefone(s.telefone || '');
    setEmail(s.email || '');
    setEndereco(s.endereco || '');
    setCidade(s.cidade || '');
    setEstado(s.estado || '');
    setTipoFornecedor(s.tipo_fornecedor || '');
    setFormError(null);
    setXmlPreview(null);
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const payload: Partial<Fornecedor> = {
      nome,
      razao_social: razaoSocial || undefined,
      cnpj: cnpj || undefined,
      telefone: telefone || undefined,
      email: email || undefined,
      endereco: endereco || undefined,
      cidade: cidade || undefined,
      estado: estado || undefined,
      tipo_fornecedor: tipoFornecedor || undefined,
    };

    try {
      if (editId) {
        await suppliersApi.update(editId, payload);
      } else {
        await suppliersApi.create(payload);
      }
      setShowModal(false);
      setXmlPreview(null);
      fetchSuppliers();
    } catch (err: any) {
      setFormError(err.response?.data?.error || 'Erro ao salvar fornecedor');
    }
  };

  const handleDelete = async (s: Fornecedor) => {
    if (!window.confirm(`Excluir fornecedor "${s.nome}"?`)) return;
    try {
      await suppliersApi.remove(s.id);
      fetchSuppliers();
    } catch (err: any) {
      window.alert(err.response?.data?.error || 'Erro ao excluir fornecedor');
    }
  };

  // XML autofill for form
  const handleXMLAutofill = async (file: File) => {
    setFormError(null);
    try {
      const data = await suppliersApi.parseXML(file);
      setXmlPreview(data);
      if (!data.nome && !data.cnpj) {
        setFormError('Não foi possível extrair os dados do emitente do XML.');
        return;
      }
      if (data.nome) setNome(data.nome);
      if (data.razao_social) setRazaoSocial(data.razao_social);
      if (data.cnpj) setCnpj(data.cnpj);
      if (data.telefone) setTelefone(data.telefone);
      if (data.endereco) setEndereco(data.endereco);
      if (data.cidade) setCidade(data.cidade);
      if (data.estado) setEstado(data.estado);
    } catch (err: any) {
      setXmlPreview(null);
      setFormError(normalizeXMLImportError(err.response?.data?.error));
    }
  };

  // Invoices
  const openInvoices = async (s: Fornecedor) => {
    setInvoiceSupplier(s);
    setInvoices([]);
    setInvoiceDetail(null);
    setInvoiceError(null);
    try {
      const data = await suppliersApi.listInvoices(s.id);
      setInvoices(data);
    } catch (err) {
      console.error(err);
    }
  };

  const showInvoiceDetail = async (invoiceId: number) => {
    setInvoiceError(null);
    try {
      const data = await suppliersApi.getInvoice(invoiceId);
      setInvoiceDetail(data);
    } catch (err: any) {
      setInvoiceError(err.response?.data?.error || 'Erro ao carregar nota fiscal');
    }
  };

  const handleUploadInvoice = async (file: File) => {
    if (!invoiceSupplier) return;
    setInvoiceError(null);
    try {
      await suppliersApi.uploadInvoice(invoiceSupplier.id, file);
      const data = await suppliersApi.listInvoices(invoiceSupplier.id);
      setInvoices(data);
    } catch (err: any) {
      setInvoiceError(normalizeXMLImportError(err.response?.data?.error || 'Erro ao processar XML da nota'));
    }
  };

  const handleDeleteInvoice = async (invoiceId: number) => {
    if (!window.confirm('Excluir esta nota fiscal?')) return;
    setInvoiceError(null);
    try {
      await suppliersApi.deleteInvoice(invoiceId);
      setInvoiceDetail(null);
      if (invoiceSupplier) {
        const data = await suppliersApi.listInvoices(invoiceSupplier.id);
        setInvoices(data);
      }
    } catch (err: any) {
      setInvoiceError(err.response?.data?.error || 'Erro ao excluir nota fiscal');
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">
            Fornecedores
          </h1>
          <p className="text-brand-muted text-sm mt-1">
            Cadastro de fornecedores e notas fiscais (NF-e).
          </p>
        </div>

        {manage && (
          <button
            onClick={openCreateModal}
            className="bg-brand-primary hover:bg-brand-primary/90 text-brand-dark font-bold font-mono px-4 py-2.5 uppercase tracking-wider text-xs flex items-center space-x-1.5 transition-colors"
          >
            <Plus size={16} />
            <span>Novo Fornecedor</span>
          </button>
        )}
      </div>

      {/* Table */}
      <div className="border border-brand-border bg-brand-card">
        {loading ? (
          <div className="p-12 text-center flex flex-col items-center justify-center space-y-4">
            <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent animate-spin" />
            <span className="font-mono text-xs text-brand-muted uppercase">Carregando fornecedores...</span>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  <th className="p-4">Fornecedor</th>
                  <th className="p-4">CNPJ</th>
                  <th className="p-4">Contato</th>
                  <th className="p-4">Localização</th>
                  <th className="p-4">Tipo</th>
                  {manage && <th className="p-4 text-right">Ações</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/60 text-sm">
                {suppliers.map((s) => (
                  <tr key={s.id} className="hover:bg-brand-dark/10">
                    <td className="p-4">
                      <div className="font-medium text-brand-text">{s.nome}</div>
                      <div className="text-xs text-brand-muted">{s.razao_social || '—'}</div>
                    </td>
                    <td className="p-4 font-mono text-xs">{s.cnpj || '—'}</td>
                    <td className="p-4">
                      <div className="text-brand-text">{s.email || '—'}</div>
                      <div className="text-xs text-brand-muted">{s.telefone || '—'}</div>
                    </td>
                    <td className="p-4">
                      <div className="text-brand-text">{s.cidade || '—'}{s.estado ? ` / ${s.estado}` : ''}</div>
                      <div className="text-xs text-brand-muted">{s.endereco || '—'}</div>
                    </td>
                    <td className="p-4">
                      <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 border border-brand-border bg-brand-dark/30">
                        {s.tipo_fornecedor || '—'}
                      </span>
                    </td>
                    {manage && (
                      <td className="p-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => openInvoices(s)}
                          title="Notas fiscais"
                          className="text-brand-primary hover:bg-brand-primary/10 border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2"
                        >
                          <FileText size={12} className="inline mr-1" />
                          NF-e
                        </button>
                        <button
                          onClick={() => openEditModal(s)}
                          title="Editar"
                          className="text-brand-primary hover:bg-brand-primary/10 border border-brand-primary/30 px-2.5 py-1.5 font-mono text-xs uppercase mr-2"
                        >
                          <Edit2 size={12} className="inline mr-1" />
                          Editar
                        </button>
                        <button
                          onClick={() => handleDelete(s)}
                          title="Excluir"
                          className="text-red-400 hover:bg-red-500/10 border border-red-500/30 px-2.5 py-1.5 font-mono text-xs uppercase"
                        >
                          <Trash2 size={12} className="inline mr-1" />
                          Excluir
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
                {suppliers.length === 0 && (
                  <tr>
                    <td colSpan={6} className="p-12 text-center text-brand-muted font-mono text-sm">
                      Nenhum fornecedor cadastrado.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Supplier Form Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-2xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                {editId ? 'Editar Fornecedor' : 'Novo Fornecedor'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-brand-muted hover:text-brand-text">
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
                    Nome do Fornecedor *
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
                    Razão Social
                  </label>
                  <input
                    type="text"
                    value={razaoSocial}
                    onChange={(e) => setRazaoSocial(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    CNPJ
                  </label>
                  <input
                    type="text"
                    value={cnpj}
                    onChange={(e) => setCnpj(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Telefone
                  </label>
                  <input
                    type="text"
                    value={telefone}
                    onChange={(e) => setTelefone(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    E-mail
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Tipo de Fornecedor
                  </label>
                  <input
                    type="text"
                    value={tipoFornecedor}
                    onChange={(e) => setTipoFornecedor(e.target.value)}
                    placeholder="Ex: TI, Material de escritório..."
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                  Endereço
                </label>
                <input
                  type="text"
                  value={endereco}
                  onChange={(e) => setEndereco(e.target.value)}
                  className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Cidade
                  </label>
                  <input
                    type="text"
                    value={cidade}
                    onChange={(e) => setCidade(e.target.value)}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-1.5">
                    Estado (UF)
                  </label>
                  <input
                    type="text"
                    maxLength={2}
                    value={estado}
                    onChange={(e) => setEstado(e.target.value.toUpperCase())}
                    className="w-full bg-brand-dark border border-brand-border px-3 py-2 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono"
                  />
                </div>
              </div>

              {/* XML Autofill */}
              <div className="border border-brand-border bg-brand-dark/20 p-4">
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-2">
                  Importar XML de NF-e (preenchimento automático)
                </label>
                <input
                  type="file"
                  accept=".xml"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleXMLAutofill(file);
                  }}
                  className="w-full text-xs font-mono text-brand-muted file:mr-3 file:border file:border-brand-primary/30 file:bg-transparent file:text-brand-primary file:px-3 file:py-1.5 file:font-mono file:text-xs file:uppercase"
                />
              </div>

              {xmlPreview && (
                <div className="border border-brand-border bg-brand-dark/20 p-4 space-y-4">
                  <div className="flex items-center justify-between gap-3 border-b border-brand-border pb-3">
                    <div>
                      <div className="text-xs font-mono uppercase tracking-wider text-brand-muted">Pré-visualização da NF-e</div>
                      <div className="text-sm text-brand-text mt-1">{xmlPreview.emitente_nome || xmlPreview.nome || 'Emitente não identificado'}</div>
                    </div>
                    <span className="text-[10px] font-mono uppercase px-2 py-1 border border-brand-primary/30 text-brand-primary">
                      Nota {xmlPreview.numero_nota || 'N/A'}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <div className="text-[11px] font-mono uppercase tracking-wider text-brand-muted">Emissão</div>
                      <div className="text-brand-text">{formatDateTime(xmlPreview.data_emissao)}</div>
                    </div>
                    <div>
                      <div className="text-[11px] font-mono uppercase tracking-wider text-brand-muted">Valor total</div>
                      <div className="text-brand-text font-mono">{formatCurrency(xmlPreview.valor_total)}</div>
                    </div>
                    <div>
                      <div className="text-[11px] font-mono uppercase tracking-wider text-brand-muted">Natureza da operação</div>
                      <div className="text-brand-text">{xmlPreview.natureza_operacao || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-[11px] font-mono uppercase tracking-wider text-brand-muted">Destinatário</div>
                      <div className="text-brand-text">{xmlPreview.destinatario_nome || 'N/A'}</div>
                    </div>
                  </div>

                  <div>
                    <div className="text-[11px] font-mono uppercase tracking-wider text-brand-muted mb-2">
                      Itens da nota ({xmlPreview.itens?.length ?? 0})
                    </div>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {xmlPreview.itens?.map((item, index) => (
                        <div key={`${item.codigo || item.descricao || 'item'}-${index}`} className="border border-brand-border bg-brand-card/60 p-3 text-xs">
                          <div className="text-brand-text">{item.descricao || item.codigo || 'Item sem descrição'}</div>
                          <div className="text-brand-muted font-mono mt-1">
                            cod: {item.codigo || '—'} · ncm: {item.ncm || '—'} · qtd: {item.quantidade ?? '—'} · unit: {formatCurrency(item.valor_unitario)} · total: {formatCurrency(item.valor_total)}
                          </div>
                        </div>
                      ))}
                      {(!xmlPreview.itens || xmlPreview.itens.length === 0) && (
                        <div className="text-brand-muted text-xs">Nenhum item foi extraído desta NF-e.</div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-4 border-t border-brand-border">
                <button
                  type="button"
                  onClick={() => { setShowModal(false); setXmlPreview(null); }}
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

      {/* Invoices Modal */}
      {invoiceSupplier && (
        <div className="fixed inset-0 bg-brand-dark/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-3xl border border-brand-border bg-brand-card p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-brand-border pb-4">
              <h3 className="text-lg font-bold font-mono uppercase tracking-wider text-brand-text">
                NF-e — {invoiceSupplier.nome}
              </h3>
              <button onClick={() => setInvoiceSupplier(null)} className="text-brand-muted hover:text-brand-text">
                <X size={20} />
              </button>
            </div>

            {invoiceError && (
              <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
                <ShieldAlert size={16} />
                <span>{invoiceError}</span>
              </div>
            )}

            {manage && (
              <div className="border border-brand-border bg-brand-dark/20 p-4">
                <label className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-2">
                  Importar XML de NF-e para este fornecedor
                </label>
                <input
                  type="file"
                  accept=".xml"
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleUploadInvoice(file);
                    e.target.value = '';
                  }}
                  className="w-full text-xs font-mono text-brand-muted file:mr-3 file:border file:border-brand-primary/30 file:bg-transparent file:text-brand-primary file:px-3 file:py-1.5 file:font-mono file:text-xs file:uppercase"
                />
              </div>
            )}

            <div className="grid grid-cols-2 gap-6">
              {/* Invoice list */}
              <div className="border border-brand-border">
                <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  Notas fiscais ({invoices.length})
                </div>
                <div className="divide-y divide-brand-border/60 max-h-72 overflow-y-auto">
                  {invoices.map((nf) => (
                    <button
                      key={nf.id}
                      onClick={() => showInvoiceDetail(nf.id)}
                      className="w-full text-left p-3 hover:bg-brand-dark/10 flex items-center justify-between"
                    >
                      <span className="font-mono text-xs text-brand-text flex items-center">
                        <FileText size={12} className="mr-2 text-brand-primary" />
                        Nota #{nf.numero_nota}
                      </span>
                      {manage && (
                        <span
                          role="button"
                          title="Excluir nota"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteInvoice(nf.id);
                          }}
                          className="text-red-400 hover:bg-red-500/10 border border-red-500/30 px-2 py-1"
                        >
                          <Trash2 size={12} />
                        </span>
                      )}
                    </button>
                  ))}
                  {invoices.length === 0 && (
                    <div className="p-6 text-center text-brand-muted font-mono text-xs">
                      Nenhuma nota fiscal cadastrada.
                    </div>
                  )}
                </div>
              </div>

              {/* Invoice detail */}
              <div className="border border-brand-border">
                <div className="p-3 border-b border-brand-border bg-brand-dark/20 text-xs font-mono uppercase tracking-wider text-brand-muted">
                  Detalhes da nota
                </div>
                {invoiceDetail ? (
                  <div className="p-4 space-y-3 text-sm">
                    <div>
                      <span className="text-brand-muted font-mono text-xs uppercase">Número:</span>
                      <div className="text-brand-text font-mono">{invoiceDetail.numero_nota}</div>
                    </div>
                    <div>
                      <span className="text-brand-muted font-mono text-xs uppercase">Emissão:</span>
                      <div className="text-brand-text">
                        {invoiceDetail.data_emissao
                          ? new Date(invoiceDetail.data_emissao).toLocaleString('pt-BR')
                          : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <span className="text-brand-muted font-mono text-xs uppercase">Natureza da operação:</span>
                      <div className="text-brand-text">{invoiceDetail.natureza_operacao || 'N/A'}</div>
                    </div>
                    <div>
                      <span className="text-brand-muted font-mono text-xs uppercase">Valor total:</span>
                      <div className="text-brand-text font-mono">
                        {invoiceDetail.valor_total != null
                          ? `R$ ${invoiceDetail.valor_total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                          : 'N/A'}
                      </div>
                    </div>
                    <div>
                      <span className="text-brand-muted font-mono text-xs uppercase">Emitente:</span>
                      <div className="text-brand-text">{invoiceDetail.emitente_nome || 'N/A'}</div>
                    </div>
                    <div>
                      <span className="text-brand-muted font-mono text-xs uppercase">Itens ({invoiceDetail.itens.length}):</span>
                      <div className="mt-2 space-y-2 max-h-40 overflow-y-auto">
                        {invoiceDetail.itens.map((item, i) => (
                          <div key={i} className="border border-brand-border bg-brand-dark/20 p-2 text-xs">
                            <div className="text-brand-text">{item.descricao || item.codigo || '—'}</div>
                            <div className="text-brand-muted font-mono">
                              qtd: {item.quantidade ?? '—'} · unit: R${' '}
                              {item.valor_unitario != null ? item.valor_unitario.toLocaleString('pt-BR') : '—'} ·
                              total: R${' '}
                              {item.valor_total != null ? item.valor_total.toLocaleString('pt-BR') : '—'}
                            </div>
                          </div>
                        ))}
                        {invoiceDetail.itens.length === 0 && (
                          <div className="text-brand-muted text-xs">Sem itens extraídos.</div>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="p-6 text-center text-brand-muted font-mono text-xs">
                    Selecione uma nota fiscal para ver os detalhes.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
