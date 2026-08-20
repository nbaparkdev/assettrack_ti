import React, { useState, useEffect } from 'react';
import { getSettings, updateSettings } from '../api/settings';
import type { SystemSettings, UpdateSettingsPayload } from '../types/settings';
import { Save, AlertCircle } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<SystemSettings>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const data = await getSettings();
      setSettings(data);
      const aiEnabled = data.ai_enabled !== 'false';
      localStorage.setItem('assettrack-ai-enabled', String(aiEnabled));
      window.dispatchEvent(new CustomEvent('assettrack-ai-visibility-change', { detail: { enabled: aiEnabled } }));
    } catch (err) {
      setError('Falha ao carregar configurações.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    let finalValue = value;
    
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      finalValue = checked ? 'true' : 'false';
    }

    if (name === 'ai_enabled') {
      const enabled = finalValue === 'true';
      localStorage.setItem('assettrack-ai-enabled', String(enabled));
      window.dispatchEvent(new CustomEvent('assettrack-ai-visibility-change', { detail: { enabled } }));
    }

    setSettings(prev => ({
      ...prev,
      [name]: finalValue
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccessMsg(null);

    try {
      const payload: UpdateSettingsPayload = { ...settings };
      await updateSettings(payload);
      setSuccessMsg('Configurações salvas com sucesso!');
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err) {
      setError('Erro ao salvar as configurações.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-4 text-brand-muted">Carregando configurações...</div>;

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-white font-mono uppercase">Configurações do Sistema</h1>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 bg-brand-primary text-white px-4 py-2 hover:bg-brand-primary/80 disabled:opacity-50 transition-colors font-mono uppercase tracking-wider text-sm border border-brand-primary"
        >
          <Save size={18} />
          {saving ? 'Salvando...' : 'Salvar Alterações'}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 flex items-center gap-2">
          <AlertCircle size={20} />
          <span className="font-mono text-sm">{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="app-notice--success bg-green-500/10 border border-green-500/50 text-green-500 p-4 flex items-center gap-2">
          <CheckCircleIcon size={20} />
          <span className="font-mono text-sm">{successMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Modules Config */}
        <div className="bg-brand-card p-6 border border-brand-border">
          <h2 className="text-lg font-semibold text-brand-primary mb-4 border-b border-brand-border pb-2 font-mono uppercase">Módulos Ativos</h2>
          
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer group">
              <input
                type="checkbox"
                name="preventive_maintenance_enabled"
                checked={settings.preventive_maintenance_enabled === 'true'}
                onChange={handleInputChange}
                className="w-5 h-5 accent-brand-primary bg-brand-dark border-brand-border"
              />
              <span className="text-brand-text group-hover:text-brand-primary transition-colors">Manutenção Preventiva</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer group">
              <input
                type="checkbox"
                name="purchases_enabled"
                checked={settings.purchases_enabled === 'true'}
                onChange={handleInputChange}
                className="w-5 h-5 accent-brand-primary bg-brand-dark border-brand-border"
              />
              <span className="text-brand-text group-hover:text-brand-primary transition-colors">Módulo de Compras</span>
            </label>

            <label className="flex items-center gap-3 cursor-pointer group">
              <input
                type="checkbox"
                name="kanban_enabled"
                checked={settings.kanban_enabled === 'true'}
                onChange={handleInputChange}
                className="w-5 h-5 accent-brand-primary bg-brand-dark border-brand-border"
              />
              <span className="text-brand-text group-hover:text-brand-primary transition-colors">Kanban de Projetos</span>
            </label>
          </div>
        </div>

        {/* AI Config */}
        <div className="bg-brand-card p-6 border border-brand-border">
          <h2 className="text-lg font-semibold text-brand-primary mb-4 border-b border-brand-border pb-2 font-mono uppercase">Assistente IA</h2>
          
          <div className="space-y-4">
            <label className="flex items-center gap-3 cursor-pointer group mb-4">
              <input
                type="checkbox"
                name="ai_enabled"
                checked={settings.ai_enabled === 'true'}
                onChange={handleInputChange}
                className="w-5 h-5 accent-brand-primary bg-brand-dark border-brand-border"
              />
              <span className="text-brand-text font-medium group-hover:text-brand-primary transition-colors">Ativar Assistente IA</span>
            </label>

            {settings.ai_enabled === 'true' && (
              <>
                <div>
                  <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">Provedor de IA</label>
                  <select
                    name="ai_provider"
                    value={settings.ai_provider || 'openai'}
                    onChange={handleInputChange}
                    className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors appearance-none"
                  >
                    <option value="openai" className="bg-brand-dark text-brand-text">OpenAI</option>
                    <option value="gemini" className="bg-brand-dark text-brand-text">Google Gemini</option>
                    <option value="ollama" className="bg-brand-dark text-brand-text">Ollama (Local)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">Chave de API (OpenAI)</label>
                  <input
                    type="password"
                    name="openai_api_key"
                    value={settings.openai_api_key || ''}
                    onChange={handleInputChange}
                    className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
                  />
                </div>

                <div>
                  <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">Modelo (OpenAI)</label>
                  <input
                    type="text"
                    name="openai_model"
                    value={settings.openai_model || 'gpt-4o-mini'}
                    onChange={handleInputChange}
                    className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
                  />
                </div>
                
                <div>
                  <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">Chave de API (Gemini)</label>
                  <input
                    type="password"
                    name="gemini_api_key"
                    value={settings.gemini_api_key || ''}
                    onChange={handleInputChange}
                    className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
                  />
                </div>
              </>
            )}
          </div>
        </div>

        {/* SMTP Config */}
        <div className="bg-brand-card p-6 border border-brand-border md:col-span-2">
          <h2 className="text-lg font-semibold text-brand-primary mb-4 border-b border-brand-border pb-2 font-mono uppercase">Servidor SMTP (Envio de E-mails)</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">SMTP Host</label>
              <input
                type="text"
                name="smtp_host"
                placeholder="smtp.gmail.com"
                value={settings.smtp_host || ''}
                onChange={handleInputChange}
                className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
              />
            </div>
            <div>
              <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">SMTP Port</label>
              <input
                type="text"
                name="smtp_port"
                placeholder="587"
                value={settings.smtp_port || ''}
                onChange={handleInputChange}
                className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
              />
            </div>
            <div>
              <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">SMTP User / E-mail</label>
              <input
                type="text"
                name="smtp_user"
                value={settings.smtp_user || ''}
                onChange={handleInputChange}
                className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
              />
            </div>
            <div>
              <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">SMTP Password</label>
              <input
                type="password"
                name="smtp_password"
                value={settings.smtp_password || ''}
                onChange={handleInputChange}
                className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm text-brand-muted mb-1 font-mono uppercase">Remetente (From Name)</label>
              <input
                type="text"
                name="smtp_from"
                placeholder="Assettrack TI <noreply@assettrack.com>"
                value={settings.smtp_from || ''}
                onChange={handleInputChange}
                className="w-full p-2.5 bg-brand-dark border border-brand-border text-brand-text focus:outline-none focus:border-brand-primary transition-colors placeholder-brand-muted/30"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function CheckCircleIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}
