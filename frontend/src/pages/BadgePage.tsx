import React, { useState, useEffect } from 'react';
import { usersApi } from '../api/users';
import { toApiFileUrl } from '../api/client';
import type { BadgeInfo, QRTokenInfo } from '../types';
import { QrCode, RefreshCw, KeyRound, CheckCircle, AlertCircle, Copy } from 'lucide-react';

export const BadgePage: React.FC = () => {
  const [badge, setBadge] = useState<BadgeInfo | null>(null);
  const [qrInfo, setQrInfo] = useState<QRTokenInfo | null>(null);
  const [pin, setPin] = useState('');
  const [pinLoading, setPinLoading] = useState(false);
  const [pinSuccess, setPinSuccess] = useState(false);
  const [pinError, setPinError] = useState<string | null>(null);
  const [qrLoading, setQrLoading] = useState(false);

  const fetchBadgeData = async () => {
    try {
      const bData = await usersApi.getMyBadge();
      const qrData = await usersApi.getMyQR();
      setBadge(bData);
      setQrInfo(qrData);
    } catch (err) {
      console.error('Erro ao carregar crachá', err);
    }
  };

  useEffect(() => {
    fetchBadgeData();
  }, []);

  const handleRegenerateQR = async () => {
    setQrLoading(true);
    try {
      const data = await usersApi.regenerateQR();
      setQrInfo(data);
      if (badge) {
        setBadge({ ...badge, qr_code_base64: data.qr_code_base64 });
      }
    } catch (err) {
      console.error('Erro ao regenerar QR Code', err);
    } finally {
      setQrLoading(false);
    }
  };

  const handleSetPIN = async (e: React.FormEvent) => {
    e.preventDefault();
    setPinLoading(true);
    setPinError(null);
    setPinSuccess(false);
    try {
      await usersApi.setPIN(pin);
      setPinSuccess(true);
      setPin('');
      if (qrInfo) {
        setQrInfo({ ...qrInfo, has_pin: true });
      }
    } catch (err: any) {
      setPinError(err.response?.data?.detail || 'Erro ao configurar PIN');
    } finally {
      setPinLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold uppercase tracking-wider font-mono text-brand-text m-0">
          Crachá Digital
        </h1>
        <p className="text-brand-muted text-sm mt-1">
          Gerencie seu código de identificação institucional e PIN de segurança.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
        {/* Badge Card */}
        <div className="border border-brand-border bg-brand-card p-8 flex flex-col items-center">
          <span className="font-mono text-xs text-brand-primary uppercase tracking-widest mb-6">
            Identidade Funcional
          </span>

          <div className="w-full max-w-xs border border-brand-border bg-brand-dark p-6 text-center flex flex-col items-center space-y-4">
            <div className="w-20 h-20 border border-brand-primary/30 overflow-hidden flex items-center justify-center font-mono text-brand-primary text-3xl bg-brand-primary/5 uppercase shadow-sm">
              {badge?.avatar_url ? (
                <img
                  src={toApiFileUrl(badge.avatar_url)}
                  alt={`Avatar de ${badge.nome}`}
                  className="w-full h-full object-cover"
                />
              ) : (
                badge?.nome.substring(0, 2)
              )}
            </div>

            <div>
              <h3 className="font-bold text-lg text-brand-text truncate w-full">{badge?.nome}</h3>
              <p className="text-xs font-mono text-brand-primary uppercase tracking-wider mt-1">
                {badge?.cargo || 'Colaborador'}
              </p>
              <p className="text-xs text-brand-muted mt-0.5">{badge?.departamento_nome || 'Sem Departamento'}</p>
            </div>

            <div className="w-full border-t border-brand-border/60 my-2" />

            {/* QR base64 */}
            {badge?.qr_code_base64 ? (
              <div className="flex flex-col items-center space-y-3 w-full">
                <div className="bg-white p-2 border border-brand-border select-none">
                  <img
                    src={`data:image/png;base64,${badge.qr_code_base64}`}
                    alt="QR Code do Usuário"
                    className="w-full h-full object-contain"
                  />
                </div>
                {qrInfo?.qr_token && (
                  <button
                    onClick={() => navigator.clipboard.writeText(qrInfo.qr_token)}
                    className="flex items-center space-x-2 text-[10px] font-mono text-brand-muted hover:text-brand-primary hover:bg-brand-primary/10 border border-brand-border hover:border-brand-primary/50 px-3 py-1.5 transition-all w-full justify-center group"
                    title="Copiar Token"
                  >
                    <span className="truncate">{qrInfo.qr_token}</span>
                    <Copy size={12} className="opacity-50 group-hover:opacity-100 flex-shrink-0" />
                  </button>
                )}
              </div>
            ) : (
              <div className="w-40 h-40 bg-brand-card flex items-center justify-center border border-brand-border/60">
                <div className="w-8 h-8 border-2 border-brand-primary border-t-transparent animate-spin" />
              </div>
            )}

            <div className="text-left w-full space-y-1 mt-4">
              <div className="flex justify-between text-[10px] font-mono text-brand-muted uppercase">
                <span>Matrícula:</span>
                <span className="text-brand-text">{badge?.matricula || 'N/D'}</span>
              </div>
              <div className="flex justify-between text-[10px] font-mono text-brand-muted uppercase">
                <span>E-mail:</span>
                <span className="text-brand-text truncate max-w-[180px]">{badge?.email}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Security Controls */}
        <div className="space-y-6">
          {/* QR Actions */}
          <div className="border border-brand-border bg-brand-card p-6 space-y-4">
            <div className="flex items-center space-x-2 text-brand-primary">
              <QrCode size={18} />
              <h3 className="font-bold font-mono text-sm uppercase tracking-wider">
                Segurança do QR Code
              </h3>
            </div>
            <p className="text-xs text-brand-muted leading-relaxed">
              O token de acesso do QR Code é regenerado automaticamente a cada 90 dias. Caso suspeite de vazamento, regenere o token imediatamente.
            </p>
            <div className="flex items-center justify-between text-[10px] font-mono border-t border-b border-brand-border py-2 text-brand-muted">
              <span>Status do PIN:</span>
              <span className={qrInfo?.has_pin ? 'text-brand-primary font-bold' : 'text-red-400 font-bold'}>
                {qrInfo?.has_pin ? 'PIN CONFIGURADO' : 'PIN PENDENTE'}
              </span>
            </div>
            <button
              onClick={handleRegenerateQR}
              disabled={qrLoading}
              className="w-full border border-brand-primary hover:bg-brand-primary/10 text-brand-primary font-bold font-mono py-2.5 uppercase tracking-wider text-xs flex items-center justify-center space-x-2 transition-colors disabled:opacity-50"
            >
              <RefreshCw size={14} className={qrLoading ? 'animate-spin' : ''} />
              <span>Regenerar QR Token</span>
            </button>
          </div>

          {/* PIN Setup */}
          <div className="border border-brand-border bg-brand-card p-6 space-y-4">
            <div className="flex items-center space-x-2 text-brand-primary">
              <KeyRound size={18} />
              <h3 className="font-bold font-mono text-sm uppercase tracking-wider">
                Configurar PIN de Acesso
              </h3>
            </div>
            <p className="text-xs text-brand-muted leading-relaxed">
              Defina um código numérico de 4 a 6 dígitos para validar transações físicas e confirmações de entrega do QR Code.
            </p>

            {pinSuccess && (
              <div className="app-notice--success p-3 border border-brand-primary/30 bg-brand-primary/5 text-brand-primary text-xs font-mono flex items-center space-x-2">
                <CheckCircle size={14} />
                <span>PIN configurado com sucesso!</span>
              </div>
            )}

            {pinError && (
              <div className="p-3 border border-red-500/30 bg-red-500/5 text-red-400 text-xs font-mono flex items-center space-x-2">
                <AlertCircle size={14} />
                <span>{pinError}</span>
              </div>
            )}

            <form onSubmit={handleSetPIN} className="space-y-4">
              <div>
                <input
                  type="password"
                  required
                  maxLength={6}
                  value={pin}
                  onChange={(e) => setPin(e.target.value.replace(/\D/g, ''))}
                  className="w-full bg-brand-dark border border-brand-border px-4 py-3 text-sm text-brand-text focus:outline-none focus:border-brand-primary transition-colors font-mono text-center tracking-widest"
                  placeholder="DIGITE SEU PIN (4-6 NÚMEROS)"
                />
              </div>
              <button
                type="submit"
                disabled={pinLoading || pin.length < 4}
                className="w-full bg-brand-primary hover:bg-brand-primary/90 text-white font-bold font-mono py-3 rounded-[10px] uppercase tracking-wider text-xs transition-colors disabled:opacity-50 shadow-md shadow-brand-primary/20"
              >
                {pinLoading ? 'Gravando PIN...' : 'Salvar Novo PIN'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
