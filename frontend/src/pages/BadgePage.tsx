import React, { useState, useEffect } from 'react';
import { usersApi } from '../api/users';
import { toApiFileUrl } from '../api/client';
import type { BadgeInfo, QRTokenInfo } from '../types';
import { QrCode, RefreshCw, KeyRound, CheckCircle, AlertCircle, Copy, Building2 } from 'lucide-react';

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
        <div className="overflow-hidden rounded-2xl border border-brand-border bg-brand-card shadow-[0_18px_45px_rgba(23,43,77,0.12)]">
          <div className="relative flex items-center justify-between gap-4 overflow-hidden bg-[linear-gradient(135deg,#172b4d_0%,#0c66e4_100%)] px-6 py-5 text-white sm:px-8">
            <div className="pointer-events-none absolute -right-8 -top-10 h-36 w-36 rounded-full border border-white/10 bg-white/5" />
            <div className="pointer-events-none absolute right-20 top-8 h-16 w-16 rounded-full border border-white/10" />
            <div className="relative flex min-w-0 items-center gap-3">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-white/20 bg-white/10 shadow-lg shadow-black/10">
                <Building2 size={21} />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-bold uppercase tracking-[0.15em]">AssetTrack TI</p>
                <p className="mt-1 text-[10px] font-medium uppercase tracking-[0.22em] text-white/70">Identidade funcional</p>
              </div>
            </div>
            <QrCode size={24} className="relative shrink-0 text-white/85" />
          </div>

          <div className="p-6 sm:p-8">
            <div className="grid grid-cols-1 items-center gap-7 sm:grid-cols-[minmax(0,1fr)_180px]">
              <div className="flex min-w-0 items-center gap-4 sm:flex-col sm:items-start">
                <div className="h-28 w-28 shrink-0 overflow-hidden rounded-xl border-4 border-white bg-brand-primary/5 text-center font-mono text-3xl uppercase text-brand-primary shadow-[0_10px_25px_rgba(12,102,228,0.22)] ring-1 ring-brand-primary/20 sm:h-36 sm:w-36">
                  {badge?.avatar_url ? (
                    <img
                      src={toApiFileUrl(badge.avatar_url)}
                      alt={`Avatar de ${badge.nome}`}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <span className="grid h-full w-full place-items-center">{badge?.nome.substring(0, 2)}</span>
                  )}
                </div>
                <div className="min-w-0 sm:w-full">
                  <h3 className="truncate text-2xl font-bold uppercase tracking-tight text-brand-text">{badge?.nome}</h3>
                  <div className="mt-3 h-1 w-10 rounded-full bg-brand-primary" />
                  <p className="mt-3 text-xs font-mono font-semibold uppercase tracking-[0.16em] text-brand-primary">
                    {badge?.cargo || 'Colaborador'}
                  </p>
                  <p className="mt-1 text-sm text-brand-muted">{badge?.departamento_nome || 'Sem Departamento'}</p>
                </div>
              </div>

              {/* QR base64 */}
              {badge?.qr_code_base64 ? (
                <div className="flex flex-col items-center gap-3">
                  <div className="select-none rounded-xl border border-brand-border bg-white p-2 shadow-sm">
                    <img
                      src={`data:image/png;base64,${badge.qr_code_base64}`}
                      alt="QR Code do Usuário"
                      className="h-40 w-40 object-contain"
                    />
                  </div>
                  {qrInfo?.qr_token && (
                    <button
                      onClick={() => navigator.clipboard.writeText(qrInfo.qr_token)}
                      className="group flex w-full items-center justify-center gap-2 rounded-lg border border-brand-border px-3 py-2 text-[10px] font-mono text-brand-muted transition-all hover:border-brand-primary/50 hover:bg-brand-primary/10 hover:text-brand-primary"
                      title="Copiar Token"
                    >
                      <span className="truncate">{qrInfo.qr_token}</span>
                      <Copy size={12} className="shrink-0 opacity-50 group-hover:opacity-100" />
                    </button>
                  )}
                </div>
              ) : (
                <div className="grid h-40 w-40 place-items-center justify-self-center border border-brand-border/60 bg-brand-card">
                  <div className="h-8 w-8 animate-spin border-2 border-brand-primary border-t-transparent" />
                </div>
              )}
            </div>

            <div className="mt-7 grid grid-cols-1 gap-3 border-t border-brand-border pt-5 text-xs font-mono uppercase sm:grid-cols-2">
              <div>
                <span className="block text-[10px] tracking-wider text-brand-muted">Matrícula</span>
                <span className="mt-1 block font-semibold text-brand-text">{badge?.matricula || 'N/D'}</span>
              </div>
              <div className="sm:text-right">
                <span className="block text-[10px] tracking-wider text-brand-muted">E-mail</span>
                <span className="mt-1 block truncate font-semibold text-brand-text">{badge?.email}</span>
              </div>
            </div>
          </div>

          <div className="bg-[linear-gradient(90deg,#e8f1ff_0%,#f7f9fc_50%,#e8f1ff_100%)] px-6 py-3 text-center text-[10px] font-mono font-semibold uppercase tracking-[0.24em] text-brand-primary">
            {badge?.departamento_nome || 'Acesso institucional seguro'}
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
