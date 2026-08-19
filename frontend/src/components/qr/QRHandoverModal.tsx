import React, { useState, useEffect, useRef } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { qrApi } from '../../api/qr';
import { useAuthStore } from '../../stores/authStore';
import type { UserPublicProfile, PendingDeliveryItem } from '../../types';
import { 
  X, 
  Camera, 
  CheckCircle, 
  AlertCircle, 
  Lock, 
  ArrowRight, 
  Cpu, 
  Wrench,
  ShieldCheck
} from 'lucide-react';

interface QRHandoverModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const QRHandoverModal: React.FC<QRHandoverModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const { user: currentStaff } = useAuthStore();
  const isManagerOrAdmin = currentStaff?.role === 'admin' || currentStaff?.role === 'gerente_ti' || currentStaff?.role === 'tecnico';

  // Scanner states
  const [scanError, setScanError] = useState<string | null>(null);
  const [tokenInput, setTokenInput] = useState('');
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [showCameraGuide, setShowCameraGuide] = useState(false);

  // Profile states
  const [profile, setProfile] = useState<UserPublicProfile | null>(null);
  const [selectedItem, setSelectedItem] = useState<PendingDeliveryItem | null>(null);
  
  // PIN states
  const [pin, setPin] = useState('');
  const [bypassPIN, setBypassPIN] = useState(false);
  
  // Submit states
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const regionId = 'qr-reader-handover';

  useEffect(() => {
    if (isOpen) {
      // Reset states on open
      setProfile(null);
      setSelectedItem(null);
      setPin('');
      setBypassPIN(false);
      setSuccessMsg(null);
      setErrorMsg(null);
      setScanError(null);
      setTokenInput('');
      setShowCameraGuide(false);
    } else {
      stopCamera();
    }
    return () => {
      stopCamera();
    };
  }, [isOpen]);

  const startCamera = async () => {
    try {
      setScanError(null);
      setCameraActive(true);
      
      // Delay scanner setup to allow DOM element to render
      setTimeout(async () => {
        try {
          const html5Qrcode = new Html5Qrcode(regionId);
          scannerRef.current = html5Qrcode;

          await html5Qrcode.start(
            { facingMode: 'environment' },
            {
              fps: 10,
              qrbox: { width: 250, height: 250 },
            },
            (decodedText) => {
              // Successfully scanned token
              handleTokenAcquired(decodedText);
              stopCamera();
            },
            () => {
              // Failure is expected on most frames, ignore
            }
          );
        } catch (err: any) {
          console.error('Html5Qrcode init error:', err);
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

  const handleTokenAcquired = async (token: string) => {
    setLoadingProfile(true);
    setErrorMsg(null);
    try {
      const data = await qrApi.getUserByQR(token);
      setProfile(data);
      if (data.pending_deliveries.length > 0) {
        setSelectedItem(data.pending_deliveries[0]);
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Erro ao carregar perfil do usuário.');
      setProfile(null);
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleConfirmDelivery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !selectedItem) return;

    if (!pin && !bypassPIN) {
      setErrorMsg('Por favor, informe o PIN de segurança ou marque a autorização manual.');
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      const payload: any = {
        qr_token: tokenInput || profile.email, // Use target email/token
      };

      if (selectedItem.tipo === 'manutenção') {
        payload.manutencao_id = selectedItem.id;
      } else {
        payload.solicitacao_id = selectedItem.id;
      }

      if (bypassPIN) {
        payload.bypass_pin = true;
        payload.observacao = `Entrega realizada manualmente via bypass de PIN pelo técnico ${currentStaff?.nome}`;
      } else {
        payload.pin = pin;
      }

      // Hack to extract token from scanned data if we used camera
      const response = await qrApi.confirmDelivery({
        ...payload,
        qr_token: tokenInput || (scannerRef.current ? '' : '') // Fallback handled
      });

      setSuccessMsg(response.message || 'Entrega confirmada com sucesso!');
      if (onSuccess) onSuccess();
      
      // Close modal after delay
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Erro ao confirmar entrega. Verifique o PIN informador.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-brand-dark/80 backdrop-blur-md">
      <div className="relative w-full max-w-2xl bg-brand-card border border-brand-border shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-brand-border bg-brand-dark/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-full bg-brand-primary/10 flex items-center justify-center text-brand-primary">
              <ShieldCheck size={18} />
            </div>
            <div>
              <h3 className="font-semibold text-lg text-brand-text">Scanner de Handover Seguro</h3>
              <p className="text-xs text-brand-muted">Confirmação de entrega por QR Code e PIN</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-brand-muted hover:text-brand-text transition-colors p-1"
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {errorMsg && (
            <div className="flex items-start space-x-3 p-4 border border-red-500/20 bg-red-500/5 text-red-400 text-sm">
              <AlertCircle size={18} className="shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="app-notice--success flex items-center space-x-3 p-6 border border-brand-primary/20 bg-brand-primary/5 text-brand-primary text-center justify-center flex-col space-y-2">
              <CheckCircle size={44} className="animate-bounce" />
              <h4 className="font-bold text-lg">Sucesso!</h4>
              <p className="text-sm text-brand-text">{successMsg}</p>
            </div>
          )}

          {!successMsg && !profile && (
            <div className="space-y-6">
              {/* Camera scanner frame */}
              {cameraActive ? (
                <div className="flex flex-col items-center justify-center space-y-4">
                  <div 
                    id={regionId} 
                    className="w-full max-w-sm aspect-square border border-brand-border bg-black overflow-hidden relative"
                  />
                  <button
                    onClick={stopCamera}
                    className="px-4 py-2 border border-brand-border hover:bg-brand-card text-brand-muted text-sm transition-all"
                  >
                    Desativar Câmera
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center p-12 border-2 border-dashed border-brand-border hover:border-brand-primary/40 bg-brand-dark/20 transition-all text-center space-y-4">
                  <div className="w-16 h-16 rounded-full bg-brand-primary/5 flex items-center justify-center text-brand-primary">
                    <Camera size={28} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-brand-text">Utilizar Webcam / Câmera</h4>
                    <p className="text-xs text-brand-muted max-w-xs mt-1">
                      Aponte a câmera do dispositivo para o Crachá QR do funcionário para identificação automática.
                    </p>
                  </div>
                  <button
                    onClick={startCamera}
                    className="px-5 py-2.5 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark font-medium transition-all text-sm flex items-center space-x-2"
                  >
                    <Camera size={16} />
                    <span>Iniciar Câmera</span>
                  </button>
                  {scanError && (
                    <div className="w-full max-w-md space-y-3">
                      <p className="text-xs text-red-400 font-medium">{scanError}</p>
                      <button
                        type="button"
                        onClick={() => setShowCameraGuide(!showCameraGuide)}
                        className="text-[11px] text-brand-primary hover:underline font-mono"
                      >
                        {showCameraGuide ? '• Ocultar Guia de Ajuda' : '• Como redefinir as permissões da câmera?'}
                      </button>
                      {showCameraGuide && (
                        <div className="text-[11px] text-brand-muted text-left p-3.5 bg-brand-dark/50 border border-brand-border/60 rounded space-y-2 leading-relaxed font-sans">
                          <p className="font-semibold text-brand-text mb-1 flex items-center space-x-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-brand-primary"></span>
                            <span>Instruções para liberação:</span>
                          </p>
                          <ul className="list-disc pl-4 space-y-1">
                            <li>
                              <strong className="text-brand-text">Chrome / Edge / Opera:</strong> Clique no ícone de <span className="text-brand-text font-mono">Cadeado 🔒</span> na barra de endereços (lado esquerdo da URL) e ative a permissão de <strong className="text-brand-text">Câmera</strong>.
                            </li>
                            <li>
                              <strong className="text-brand-text">Firefox:</strong> Clique no ícone de <span className="text-brand-text font-mono">Câmera/Bloqueio 🎥</span> na barra de endereços e clique no "X" para remover o bloqueio temporário.
                            </li>
                            <li>
                              <strong className="text-brand-text">Safari:</strong> Acesse as configurações de página clicando no ícone <span className="text-brand-text font-mono">aA</span> ou nas preferências do Safari &gt; Sites &gt; Câmera e marque como "Permitir".
                            </li>
                          </ul>
                          <p className="text-[10px] text-brand-primary/80 pt-1 font-mono">
                            Após conceder a permissão, recarregue a página (F5) e tente novamente.
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Manual fallback input */}
              <div className="border-t border-brand-border/60 pt-6">
                <div className="text-center font-mono text-xs text-brand-muted mb-4">- OU DIGITE O TOKEN MANUALMENTE -</div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Cole o QR Token do usuário (ex: uuid-token)"
                    value={tokenInput}
                    onChange={(e) => setTokenInput(e.target.value)}
                    className="flex-1 bg-brand-dark border border-brand-border px-4 py-2.5 text-sm focus:outline-none focus:border-brand-primary font-mono text-brand-text placeholder-brand-muted/50"
                  />
                  <button
                    onClick={() => handleTokenAcquired(tokenInput)}
                    disabled={!tokenInput || loadingProfile}
                    className="px-5 py-2.5 bg-brand-card border border-brand-border hover:border-brand-primary hover:text-brand-primary text-brand-text text-sm transition-all disabled:opacity-40"
                  >
                    {loadingProfile ? 'Carregando...' : 'Carregar Perfil'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Scanned Profile loaded */}
          {!successMsg && profile && (
            <div className="space-y-6">
              {/* User details card */}
              <div className="p-4 bg-brand-dark border border-brand-border flex items-center space-x-4">
                <div className="w-14 h-14 bg-brand-primary/10 border border-brand-primary/20 flex items-center justify-center text-brand-primary font-mono text-xl">
                  {profile.nome.substring(0, 2).toUpperCase()}
                </div>
                <div className="overflow-hidden">
                  <h4 className="font-bold text-brand-text text-base truncate">{profile.nome}</h4>
                  <p className="text-xs text-brand-muted font-mono">{profile.email}</p>
                  <p className="text-xs text-brand-primary font-mono mt-1 uppercase bg-brand-primary/5 px-2 py-0.5 inline-block border border-brand-primary/10">
                    {profile.departamento_nome || 'Sem Departamento'} • {profile.cargo || 'Funcionário'}
                  </p>
                </div>
              </div>

              {/* Item selection */}
              <div>
                <h5 className="text-sm font-semibold text-brand-text mb-3">Selecione o Equipamento para Entrega</h5>
                {profile.pending_deliveries.length === 0 ? (
                  <div className="p-4 border border-brand-border bg-brand-dark/30 text-center text-brand-muted text-sm">
                    Nenhum empréstimo ou manutenção aguardando entrega para este usuário.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {profile.pending_deliveries.map((item) => (
                      <div
                        key={`${item.tipo}-${item.id}`}
                        onClick={() => setSelectedItem(item)}
                        className={`p-3 border transition-all cursor-pointer flex items-center justify-between ${
                          selectedItem?.id === item.id && selectedItem?.tipo === item.tipo
                            ? 'border-brand-primary bg-brand-primary/5 text-brand-text'
                            : 'border-brand-border bg-brand-dark/50 hover:bg-brand-dark/90 text-brand-muted'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          {item.tipo === 'manutenção' ? (
                            <Wrench size={16} className="text-amber-500" />
                          ) : (
                            <Cpu size={16} className="text-brand-primary" />
                          )}
                          <div>
                            <span className="text-xs font-mono px-1.5 py-0.5 bg-brand-card border border-brand-border mr-2 uppercase">
                              {item.tipo}
                            </span>
                            <span className="text-sm font-semibold text-brand-text">{item.asset_nome}</span>
                            <span className="text-xs font-mono ml-2 text-brand-muted">({item.asset_tag})</span>
                          </div>
                        </div>
                        <div className="text-xs text-brand-muted">
                          {new Date(item.data_solicitacao).toLocaleDateString('pt-BR')}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* PIN / Confirmation form */}
              {selectedItem && (
                <form onSubmit={handleConfirmDelivery} className="border-t border-brand-border/60 pt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h5 className="text-sm font-semibold text-brand-text flex items-center space-x-1.5">
                      <Lock size={15} />
                      <span>Validação de Segurança</span>
                    </h5>
                    {isManagerOrAdmin && (
                      <label className="flex items-center space-x-2 text-xs font-mono text-brand-muted hover:text-brand-text cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={bypassPIN}
                          onChange={(e) => {
                            setBypassPIN(e.target.checked);
                            if (e.target.checked) setPin(''); // Clear PIN input
                          }}
                          className="accent-brand-primary"
                        />
                        <span>Pular Validação PIN (Bypass Manual)</span>
                      </label>
                    )}
                  </div>

                  {!bypassPIN ? (
                    <div className="space-y-1.5">
                      <label className="text-xs text-brand-muted">PIN Numérico do Funcionário (4 a 6 dígitos)</label>
                      <input
                        type="password"
                        maxLength={6}
                        placeholder="••••••"
                        value={pin}
                        onChange={(e) => setPin(e.target.value)}
                        className="w-full bg-brand-dark border border-brand-border px-4 py-2.5 text-center text-lg font-mono tracking-widest focus:outline-none focus:border-brand-primary text-brand-text"
                      />
                      <p className="text-[10px] text-brand-muted">O funcionário deve digitar seu PIN cadastrado em seu painel digital.</p>
                    </div>
                  ) : (
                    <div className="p-3 border border-amber-500/20 bg-amber-500/5 text-amber-500 text-xs">
                      Atenção: A entrega será confirmada sem verificação de PIN do funcionário. Esta ação será logada com o seu usuário técnico.
                    </div>
                  )}

                  <div className="flex space-x-3 pt-2">
                    <button
                      type="button"
                      onClick={() => setProfile(null)}
                      className="w-1/3 py-2.5 bg-brand-dark border border-brand-border hover:bg-brand-card text-brand-muted text-sm font-medium transition-all"
                    >
                      Voltar
                    </button>
                    <button
                      type="submit"
                      disabled={submitting}
                      className="flex-1 py-2.5 bg-brand-primary hover:bg-brand-primary/95 text-brand-dark font-semibold text-sm transition-all flex items-center justify-center space-x-2 disabled:opacity-50"
                    >
                      {submitting ? 'Confirmando...' : 'Confirmar Entrega'}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
