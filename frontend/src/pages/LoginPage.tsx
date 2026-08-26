import React, { useState, useEffect, useRef } from 'react';
import { useAuthStore } from '../stores/authStore';
import { authApi } from '../api/auth';
import { API_BASE_URL } from '../api/client';
import { KeyRound, QrCode, AlertCircle, Settings, RotateCcw, Camera, X, CheckCircle } from 'lucide-react';
import { Html5Qrcode } from 'html5-qrcode';

export const LoginPage: React.FC = () => {
  const loginStore = useAuthStore().login;
  const [mode, setMode] = useState<'standard' | 'qr'>('standard');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [qrToken, setQrToken] = useState('');
  const [pin, setPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [qrSuccessMsg, setQrSuccessMsg] = useState<string | null>(null);

  // Connectivity Settings for mobile dev/local testing
  const [showSettings, setShowSettings] = useState(false);
  const [customApiUrl, setCustomApiUrl] = useState(
    localStorage.getItem('custom_api_url') || API_BASE_URL
  );

  const handleSaveSettings = () => {
    localStorage.setItem('custom_api_url', customApiUrl.trim());
    window.location.reload();
  };

  const handleResetSettings = () => {
    localStorage.removeItem('custom_api_url');
    window.location.reload();
  };

  // Camera Scanner configuration
  const [cameraActive, setCameraActive] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const regionId = 'qr-reader-login';

  useEffect(() => {
    return () => {
      // Clean up camera on unmount
      if (scannerRef.current && scannerRef.current.isScanning) {
        scannerRef.current.stop().catch(console.error);
      }
    };
  }, []);

  useEffect(() => {
    if (mode !== 'qr') {
      stopCamera();
    }
    setQrSuccessMsg(null);
  }, [mode]);

  const extractTokenFromQr = (text: string): string => {
    if (!text) return '';
    let trimmed = text.trim();
    
    // Remove query params or hash if any
    trimmed = trimmed.split('?')[0].split('#')[0];
    
    if (trimmed.includes('://') || trimmed.includes('/')) {
      if (trimmed.includes('/usuario/')) {
        const parts = trimmed.split('/usuario/');
        return parts[parts.length - 1];
      }
      if (trimmed.includes('token=')) {
        const parts = trimmed.split('token=');
        return parts[1]?.split('&')[0] || trimmed;
      }
      const parts = trimmed.split('/');
      return parts[parts.length - 1] || trimmed;
    }
    return trimmed;
  };

  const startCamera = async () => {
    try {
      setScanError(null);
      setCameraActive(true);
      
      setTimeout(async () => {
        try {
          const html5Qrcode = new Html5Qrcode(regionId);
          scannerRef.current = html5Qrcode;

          await html5Qrcode.start(
            { facingMode: 'environment' },
            {
              fps: 10,
              qrbox: { width: 180, height: 180 },
            },
            (decodedText) => {
              const token = extractTokenFromQr(decodedText);
              setQrToken(token);
              setQrSuccessMsg('Token lido com sucesso! Digite o PIN de Segurança para entrar.');
              stopCamera();
            },
            () => {
              // Expected frame failures can be ignored
            }
          );
        } catch (err: any) {
          console.error('Html5Qrcode login init error:', err);
          setScanError('Não foi possível iniciar a câmera. Verifique as permissões de acesso.');
          setCameraActive(false);
        }
      }, 300);
    } catch (err: any) {
      setScanError('Erro ao carregar a câmera.');
      setCameraActive(false);
    }
  };

  const stopCamera = async () => {
    if (scannerRef.current && scannerRef.current.isScanning) {
      try {
        await scannerRef.current.stop();
      } catch (err) {
        console.error('Stop scanner error:', err);
      }
      scannerRef.current = null;
    }
    setCameraActive(false);
  };

  const formatLoginError = (err: any): string => {
    const detail = err.response?.data?.detail || err.message || '';
    const lower = detail.toLowerCase();
    if (lower.includes('inactive') || lower.includes('inativo')) {
      return 'Usuario Inativo entrar em contato com TI.';
    }
    if (lower.includes('incorrect') || lower.includes('incorret')) {
      return 'E-mail ou senha incorretos.';
    }
    return detail || 'Falha ao autenticar. Tente novamente.';
  };

  const handleStandardSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await authApi.login({ username: email, password });
      await loginStore(res.access_token);
      window.location.href = '/';
    } catch (err: any) {
      setError(formatLoginError(err));
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
      setError(formatLoginError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col justify-center items-center p-4 bg-[radial-gradient(circle_at_80%_15%,rgba(255,255,255,.30),transparent_25rem),linear-gradient(135deg,#a9d4ee,#68acd3)]">
      <div className="w-full max-w-md rounded-2xl border border-white/60 bg-white/90 p-8 shadow-[0_18px_60px_rgba(9,30,66,.22)] backdrop-blur relative">
        {/* Settings Trigger Icon */}
        <button
          type="button"
          onClick={() => setShowSettings(!showSettings)}
          className="absolute top-6 right-6 p-2 rounded-xl text-brand-muted hover:text-brand-primary hover:bg-slate-100/50 transition-all duration-200"
          title="Configurações de Conexão"
        >
          <Settings size={18} className={`transition-transform duration-300 ${showSettings ? 'rotate-90' : ''}`} />
        </button>

        {/* Header */}
        <div className="text-center mb-8">
          <img
            src="/logo-assettrack-claro.svg"
            alt="AssetTrack TI"
            className="mx-auto mb-4 h-auto w-[220px] max-w-[75%] object-contain"
          />
          <h2 className="text-2xl font-bold tracking-tight text-brand-text">
            Painel de Acesso
          </h2>
        </div>

        {/* Connection Settings Panel */}
        {showSettings && (
          <div className="mb-6 p-4 rounded-xl border border-blue-500/20 bg-blue-50/50 backdrop-blur-sm space-y-3 transition-all duration-300">
            <h3 className="text-xs font-mono uppercase tracking-wider text-brand-primary font-bold">
              ⚙️ Endereço do Servidor
            </h3>
            <p className="text-[10px] text-brand-muted font-mono leading-relaxed">
              Configure a URL da API local. Exemplo: {API_BASE_URL}
            </p>
            <div className="space-y-2">
              <input
                type="text"
                value={customApiUrl}
                onChange={(e) => setCustomApiUrl(e.target.value)}
                className="w-full rounded-lg bg-white border border-brand-border px-3 py-2 text-xs font-mono text-brand-text focus:outline-none focus:border-brand-primary"
                placeholder="http://192.168.X.X:8080/api/v1"
              />
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={handleSaveSettings}
                  className="flex-1 bg-brand-primary hover:bg-brand-primary/90 text-white font-bold py-2 rounded-lg text-[10px] font-mono tracking-wider transition-colors shadow-sm cursor-pointer"
                >
                  Salvar e Conectar
                </button>
                <button
                  type="button"
                  onClick={handleResetSettings}
                  className="px-3 bg-slate-200 hover:bg-slate-300 text-brand-text rounded-lg text-[10px] flex items-center justify-center transition-colors cursor-pointer"
                  title="Restaurar Padrão"
                >
                  <RotateCcw size={12} />
                </button>
              </div>
            </div>
          </div>
        )}

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

        {/* QR Success Notification */}
        {qrSuccessMsg && (
          <div className="mb-6 p-4 border border-emerald-500/30 bg-emerald-500/5 text-emerald-600 text-xs font-mono flex items-start space-x-2 rounded-lg">
            <CheckCircle size={16} className="shrink-0 mt-0.5 text-emerald-500" />
            <span>{qrSuccessMsg}</span>
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
              
              {cameraActive ? (
                <div className="flex flex-col items-center justify-center space-y-3 mb-4 p-2 bg-slate-50 border border-brand-border rounded-xl">
                  <div 
                    id={regionId} 
                    className="w-full max-w-[220px] aspect-square border border-brand-border bg-black overflow-hidden relative rounded-lg"
                  />
                  <button
                    type="button"
                    onClick={stopCamera}
                    className="px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 text-xs font-semibold rounded-lg transition-colors flex items-center space-x-1 cursor-pointer"
                  >
                    <X size={12} />
                    <span>Desativar Câmera</span>
                  </button>
                </div>
              ) : (
                <div className="flex space-x-2">
                  <input
                    id="qr"
                    type="text"
                    required
                    value={qrToken}
                    onChange={(e) => setQrToken(e.target.value)}
                    className="flex-1 rounded-lg bg-white border border-brand-border px-4 py-3 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors"
                    placeholder="Insira o token do seu crachá"
                  />
                  <button
                    type="button"
                    onClick={startCamera}
                    className="px-3 bg-brand-primary/10 hover:bg-brand-primary/20 text-brand-primary border border-brand-primary/20 rounded-lg flex items-center justify-center transition-colors cursor-pointer"
                    title="Escanear com a Câmera"
                  >
                    <Camera size={18} />
                  </button>
                </div>
              )}
              
              {scanError && (
                <p className="text-[10px] text-red-500 font-mono mt-1">{scanError}</p>
              )}
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
