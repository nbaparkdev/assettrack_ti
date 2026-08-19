import React, { useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { authApi } from '../api/auth';
import { KeyRound, QrCode, AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const loginStore = useAuthStore().login;
  const [mode, setMode] = useState<'standard' | 'qr'>('standard');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [qrToken, setQrToken] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleStandardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.login({ username: email, password });
      await loginStore(res.access_token);
      window.location.href = '/';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Credenciais inválidas');
    } finally {
      setLoading(false);
    }
  };

  const handleQRSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.qrLogin({ qr_token: qrToken, pin });
      await loginStore(res.access_token);
      window.location.href = '/';
    } catch (err: any) {
      setError(err.response?.data?.detail || 'QR Token ou PIN incorretos');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-[radial-gradient(circle_at_80%_15%,rgba(255,255,255,.30),transparent_25rem),linear-gradient(135deg,#a9d4ee,#68acd3)]">
      <div className="w-full max-w-md rounded-2xl border border-white/60 bg-white/90 p-8 shadow-[0_18px_60px_rgba(9,30,66,.22)] backdrop-blur">
        {/* Header */}
        <div className="text-center mb-8">
          <span className="text-xs text-brand-primary uppercase tracking-widest block mb-2 font-semibold">
            ▥ AssetTrack TI
          </span>
          <h2 className="text-2xl font-bold tracking-tight text-brand-text">
            Painel de Acesso
          </h2>
        </div>

        {/* Mode Toggle */}
        <div className="flex rounded-xl border border-brand-border bg-slate-50 p-1 mb-6">
          <button
            type="button"
            onClick={() => { setMode('standard'); setError(null); }}
            className={`flex-1 py-3 text-xs font-mono uppercase tracking-wider flex items-center justify-center space-x-2 transition-all duration-150 ${
              mode === 'standard'
                ? 'bg-white text-brand-primary rounded-lg shadow-sm'
                : 'text-brand-muted hover:text-brand-text'
            }`}
          >
            <KeyRound size={14} />
            <span>Credenciais</span>
          </button>
          <button
            type="button"
            onClick={() => { setMode('qr'); setError(null); }}
            className={`flex-1 py-3 text-xs font-mono uppercase tracking-wider flex items-center justify-center space-x-2 transition-all duration-150 ${
              mode === 'qr'
                ? 'bg-white text-brand-primary rounded-lg shadow-sm'
                : 'text-brand-muted hover:text-brand-text'
            }`}
          >
            <QrCode size={14} />
            <span>QR Code + PIN</span>
          </button>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mb-6 p-4 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-start space-x-2">
            <AlertCircle size={16} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Forms */}
        {mode === 'standard' ? (
          <form onSubmit={handleStandardSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-2">
                E-mail Corporativo
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg bg-white border border-brand-border px-4 py-3 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                placeholder="usuario@example.com"
              />
            </div>
            <div>
              <label htmlFor="pass" className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-2">
                Senha de Acesso
              </label>
              <input
                id="pass"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg bg-white border border-brand-border px-4 py-3 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-brand-primary hover:bg-brand-primary/90 text-white font-bold py-3 tracking-wide text-xs transition-colors mt-6 disabled:opacity-50 shadow-sm"
            >
              {loading ? 'Processando...' : 'Autenticar'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleQRSubmit} className="space-y-4">
            <div>
              <label htmlFor="qr" className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-2">
                Token QR Code
              </label>
              <input
                id="qr"
                type="text"
                required
                value={qrToken}
                onChange={(e) => setQrToken(e.target.value)}
                className="w-full rounded-lg bg-white border border-brand-border px-4 py-3 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                placeholder="Insira o token do seu crachá"
              />
            </div>
            <div>
              <label htmlFor="pin" className="block text-xs font-mono uppercase tracking-wider text-brand-muted mb-2">
                PIN de Segurança
              </label>
              <input
                id="pin"
                type="password"
                required
                maxLength={6}
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                className="w-full rounded-lg bg-white border border-brand-border px-4 py-3 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors text-center tracking-widest"
                placeholder="••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-brand-primary hover:bg-brand-primary/90 text-white font-bold py-3 tracking-wide text-xs transition-colors mt-6 disabled:opacity-50 shadow-sm"
            >
              {loading ? 'Processando...' : 'Autenticar via QR'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};
