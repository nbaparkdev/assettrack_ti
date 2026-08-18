import React, { useState, useEffect, useRef } from 'react';
import { backupApi } from '../api/backup';
import type { BackupFile, BackupStatus } from '../api/backup';
import { Database, Download, Trash2, RefreshCw, Upload, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';

export const BackupPage: React.FC = () => {
  const { token } = useAuthStore();
  const [backups, setBackups] = useState<BackupFile[]>([]);
  const [status, setStatus] = useState<BackupStatus>({ is_running: false, progress: '' });
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchBackups = async () => {
    try {
      const data = await backupApi.list();
      setBackups(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const checkStatus = async () => {
    try {
      const st = await backupApi.getStatus();
      setStatus(st);
      if (st.is_running) {
        setTimeout(checkStatus, 3000);
      } else {
        fetchBackups();
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchBackups();
    checkStatus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleGenerate = async () => {
    try {
      await backupApi.generate();
      setStatus({ is_running: true, progress: 'Iniciando...' });
      setTimeout(checkStatus, 2000);
    } catch (err: any) {
      alert(err.response?.data?.error || 'Erro ao gerar backup');
    }
  };

  const handleDelete = async (filename: string) => {
    if (!window.confirm(`Tem certeza que deseja excluir o backup ${filename}?`)) return;
    try {
      await backupApi.delete(filename);
      fetchBackups();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Erro ao excluir');
    }
  };

  const handleRestoreClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!window.confirm('ATENÇÃO: A restauração substituirá todos os dados atuais do sistema! O banco de dados será sobreescrito com as informações do backup. Deseja prosseguir?')) {
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setUploading(true);
    try {
      const res = await backupApi.restore(file);
      alert(res.message);
      // Force reload page to clear state and re-authenticate
      window.location.reload();
    } catch (err: any) {
      alert(err.response?.data?.error || 'Erro fatal ao restaurar backup');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) return <div className="text-brand-muted font-mono text-sm">Carregando...</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0 flex items-center">
            <Database className="mr-3 text-brand-primary" size={28} />
            Backup do Sistema
          </h1>
          <p className="text-brand-muted text-sm mt-1">Gerencie cópias de segurança do banco de dados e arquivos de mídia</p>
        </div>
        <div className="flex gap-3">
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".zip"
            onChange={handleFileChange}
          />
          <button
            onClick={handleRestoreClick}
            disabled={status.is_running || uploading}
            className="border border-red-500/50 text-red-400 font-bold font-mono px-4 py-2 uppercase tracking-wider text-sm flex items-center hover:bg-red-500/10 disabled:opacity-50"
          >
            <Upload size={16} className="mr-2" />
            {uploading ? 'Restaurando...' : 'Restaurar ZIP'}
          </button>
          
          <button
            onClick={handleGenerate}
            disabled={status.is_running || uploading}
            className="bg-brand-primary text-brand-dark font-bold font-mono px-4 py-2 uppercase tracking-wider text-sm flex items-center hover:bg-brand-primary/90 disabled:opacity-50"
          >
            {status.is_running ? (
              <><RefreshCw size={16} className="mr-2 animate-spin" /> Gerando...</>
            ) : (
              <><Database size={16} className="mr-2" /> Gerar Novo Backup</>
            )}
          </button>
        </div>
      </div>

      {status.is_running && (
        <div className="border border-yellow-500/30 bg-yellow-500/10 p-4 text-yellow-400 font-mono text-sm flex items-center">
          <RefreshCw size={16} className="mr-3 animate-spin" />
          <span><strong>Processando Backup:</strong> {status.progress}</span>
        </div>
      )}

      <div className="border border-brand-border bg-brand-card">
        <div className="p-4 border-b border-brand-border text-sm font-bold font-mono uppercase tracking-wider text-brand-text flex items-center">
          Backups Disponíveis
        </div>
        
        {(!backups || backups.length === 0) ? (
          <div className="p-8 text-center text-brand-muted font-mono text-sm">
            Nenhum backup encontrado.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-brand-dark border-b border-brand-border text-brand-muted text-xs font-mono uppercase">
                  <th className="p-4 font-normal">Arquivo</th>
                  <th className="p-4 font-normal w-32">Tamanho</th>
                  <th className="p-4 font-normal w-48">Data de Criação</th>
                  <th className="p-4 font-normal w-32 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-brand-border/50 text-sm">
                {backups.map((b) => (
                  <tr key={b.filename} className="hover:bg-brand-dark/50 transition-colors">
                    <td className="p-4 font-mono text-brand-text break-all">
                      {b.filename}
                    </td>
                    <td className="p-4 font-mono text-brand-muted">
                      {formatSize(b.size)}
                    </td>
                    <td className="p-4 font-mono text-brand-muted">
                      {new Date(b.date).toLocaleString('pt-BR')}
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex justify-end gap-2">
                        <a
                          href={`${backupApi.downloadUrl(b.filename)}?token=${token}`}
                          className="p-2 border border-brand-primary/30 text-brand-primary hover:bg-brand-primary/10 transition-colors"
                          title="Download"
                          download
                        >
                          <Download size={16} />
                        </a>
                        <button
                          onClick={() => handleDelete(b.filename)}
                          className="p-2 border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-colors"
                          title="Excluir"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="p-4 bg-red-500/5 border border-red-500/20 rounded-sm">
        <h3 className="text-red-400 font-bold font-mono text-sm flex items-center mb-2 uppercase tracking-wider">
          <AlertTriangle size={16} className="mr-2" />
          Aviso Importante
        </h3>
        <p className="text-brand-muted text-xs font-mono leading-relaxed">
          Os backups gerados aqui utilizam os utilitários nativos do banco de dados e empacotam todos os arquivos de mídia enviados pelos usuários (Fotos, Notas Fiscais, PDFs). Ao restaurar um backup, <strong>todos os dados do sistema atual serão apagados e substituídos</strong> pelos dados contidos no arquivo selecionado.
          <br /><br />
          Recomenda-se realizar o download dos arquivos de backup e guardá-los em um local seguro (ex: Google Drive, S3).
        </p>
      </div>

    </div>
  );
};
