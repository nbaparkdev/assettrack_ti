import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Download, Smartphone, CheckCircle, AlertCircle, X, ExternalLink, QrCode, Sparkles, ShieldCheck } from 'lucide-react';
import { appVersionApi, type AppVersionInfo } from '../../api/appVersion';
import { APP_CONFIG } from '../../config/appVersion';

interface ApkDownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ApkDownloadModal: React.FC<ApkDownloadModalProps> = ({ isOpen, onClose }) => {
  const [versionInfo, setVersionInfo] = useState<AppVersionInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      appVersionApi.getVersion()
        .then(info => setVersionInfo(info))
        .catch(err => console.error('Erro ao buscar versão do app:', err))
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const rawDownloadUrl = appVersionApi.getDownloadUrl();
  const versionName = versionInfo?.version_name || APP_CONFIG.CURRENT_VERSION_NAME;
  const apkSize = versionInfo?.apk_size_formatted || '5.6 MB';
  const downloadFilename = versionInfo?.apk_filename || `AssetTrack-TI-v${versionName}.apk`;

  // Ensure absolute URL without duplicating origin
  const downloadUrl = rawDownloadUrl.startsWith('http://') || rawDownloadUrl.startsWith('https://')
    ? rawDownloadUrl
    : `${window.location.origin}${rawDownloadUrl.startsWith('/') ? '' : '/'}${rawDownloadUrl}`;

  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&margin=4&data=${encodeURIComponent(downloadUrl)}`;

  const handleDownloadClick = () => {
    setDownloading(true);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', downloadFilename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    setTimeout(() => {
      setDownloading(false);
    }, 2000);
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[99999] bg-[#091e42]/70 backdrop-blur-sm flex items-center justify-center p-3 sm:p-5 overflow-y-auto"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-white border border-[#d6e1ea] shadow-2xl rounded-2xl flex flex-col max-h-[92vh] my-auto overflow-hidden animate-in fade-in zoom-in-95 text-[#172b4d]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header - Styled with Brand Header Slate Blue */}
        <div className="p-4 sm:p-5 bg-[#345b7d] text-white flex items-center justify-between shrink-0 shadow-sm">
          <div className="flex items-center space-x-3.5">
            <div className="p-2.5 bg-white/20 text-white rounded-xl border border-white/30 shadow-xs flex items-center justify-center">
              <Smartphone size={24} className="text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h3 className="font-bold text-base sm:text-lg m-0 font-mono tracking-tight text-white">
                  Aplicativo Android (APK)
                </h3>
                <span className="bg-emerald-400 text-[#091e42] text-[11px] font-mono font-extrabold px-2.5 py-0.5 rounded-full shadow-xs">
                  v{versionName}
                </span>
              </div>
              <p className="text-xs text-white/85 mt-0.5 m-0 font-sans">
                AssetTrack TI Mobile para smartphones e coletores de dados Android
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors p-2 hover:bg-white/20 rounded-xl"
            title="Fechar"
            aria-label="Fechar modal"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-[#ffffff]">
          {/* Main Download Card */}
          <div className="bg-gradient-to-r from-[#edf5fa] via-[#e6f1f8] to-[#edf5fa] border border-[#c1d7e9] p-5 rounded-xl flex flex-col sm:flex-row items-center justify-between gap-4 shadow-sm">
            <div className="space-y-1 text-center sm:text-left">
              <div className="flex items-center justify-center sm:justify-start space-x-1.5 text-[#0c66e4]">
                <Sparkles size={16} />
                <span className="text-xs font-mono font-bold uppercase tracking-wider">Versão Oficial de Produção</span>
              </div>
              <h4 className="text-lg font-bold text-[#172b4d] m-0">AssetTrack TI Mobile</h4>
              <p className="text-xs text-[#5e6c84] m-0 font-sans">
                Tamanho do arquivo: <strong className="text-[#0c66e4] font-mono font-bold">{apkSize}</strong> • Requer {APP_CONFIG.PLATFORM_ANDROID}
              </p>
            </div>

            <button
              type="button"
              onClick={handleDownloadClick}
              disabled={loading}
              className="w-full sm:w-auto px-6 py-3.5 bg-[#0c66e4] hover:bg-[#0052cc] active:scale-95 text-white font-bold text-sm uppercase tracking-wider font-mono transition-all flex items-center justify-center space-x-2 shadow-md hover:shadow-lg shrink-0 rounded-xl cursor-pointer border-none"
            >
              <Download size={18} className={`text-white ${downloading ? 'animate-bounce' : ''}`} />
              <span className="text-white font-black">{downloading ? 'Iniciando Download...' : 'Baixar APK Direto'}</span>
            </button>
          </div>

          {/* QR Code and Mobile Fast Download Section */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-center bg-[#f4f5f7] border border-[#d6e1ea] p-4 rounded-xl">
            <div className="md:col-span-4 flex flex-col items-center justify-center p-3 bg-white rounded-lg border border-[#c1d7e9] shadow-sm">
              <img
                src={qrCodeUrl}
                alt="QR Code para Download do APK"
                className="w-32 h-32 object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
              <span className="text-[11px] font-mono text-[#172b4d] font-bold mt-1.5 flex items-center space-x-1">
                <QrCode size={13} className="text-[#0c66e4]" />
                <span>Escanear no Celular</span>
              </span>
            </div>

            <div className="md:col-span-8 space-y-2 text-left">
              <div className="flex items-center space-x-2">
                <Smartphone size={16} className="text-[#0c66e4]" />
                <h5 className="text-xs font-bold font-mono uppercase text-[#172b4d] m-0">Instalar direto no Celular</h5>
              </div>
              <p className="text-xs text-[#44546f] leading-relaxed m-0 font-sans">
                Aponte a câmera do seu smartphone Android para o QR Code ao lado para fazer o download e a instalação imediatamente no aparelho sem precisar de cabos ou computador.
              </p>
              <div className="pt-1">
                <a
                  href={downloadUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center space-x-1.5 text-xs text-[#0c66e4] hover:text-[#0052cc] hover:underline font-mono bg-white px-2.5 py-1.5 rounded-lg border border-[#d6e1ea] shadow-2xs font-semibold"
                >
                  <span>Link direto: {downloadUrl}</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </div>
          </div>

          {/* Release Notes / Novidades */}
          {versionInfo?.release_notes && (
            <div className="space-y-2 text-left">
              <div className="flex items-center space-x-2 border-b border-[#d6e1ea] pb-1.5">
                <ShieldCheck size={16} className="text-[#0c66e4]" />
                <h5 className="text-xs font-bold font-mono uppercase text-[#172b4d] m-0">
                  Novidades da Versão {versionName}
                </h5>
              </div>
              <div className="p-3.5 bg-[#f4f5f7] border border-[#d6e1ea] rounded-xl">
                <pre className="text-xs text-[#2c3e5d] whitespace-pre-wrap font-sans leading-relaxed m-0 font-normal">
                  {versionInfo.release_notes}
                </pre>
              </div>
            </div>
          )}

          {/* Step-by-Step Installation Guide */}
          <div className="space-y-2 text-left">
            <h5 className="text-xs font-bold font-mono uppercase text-[#172b4d] m-0 flex items-center space-x-1.5">
              <AlertCircle size={15} className="text-amber-600" />
              <span>Como Instalar no seu Android (3 Passos Simples)</span>
            </h5>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 bg-[#f4f5f7] border border-[#d6e1ea] rounded-xl space-y-1">
                <div className="flex items-center space-x-1.5 text-[#0c66e4] font-mono font-bold text-xs">
                  <CheckCircle size={14} />
                  <span>1. Baixar o APK</span>
                </div>
                <p className="text-[11px] text-[#44546f] leading-snug m-0 font-sans">
                  Clique no botão azul acima ou leia o QR Code com a câmera do celular.
                </p>
              </div>

              <div className="p-3 bg-[#f4f5f7] border border-[#d6e1ea] rounded-xl space-y-1">
                <div className="flex items-center space-x-1.5 text-[#0c66e4] font-mono font-bold text-xs">
                  <CheckCircle size={14} />
                  <span>2. Abrir o Arquivo</span>
                </div>
                <p className="text-[11px] text-[#44546f] leading-snug m-0 font-sans">
                  Toque na notificação de download concluído ou na pasta Downloads do celular.
                </p>
              </div>

              <div className="p-3 bg-[#f4f5f7] border border-[#d6e1ea] rounded-xl space-y-1">
                <div className="flex items-center space-x-1.5 text-[#0c66e4] font-mono font-bold text-xs">
                  <CheckCircle size={14} />
                  <span>3. Permitir e Instalar</span>
                </div>
                <p className="text-[11px] text-[#44546f] leading-snug m-0 font-sans">
                  Se o Android perguntar, permita &ldquo;Instalar de fontes desconhecidas&rdquo;.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#d6e1ea] bg-[#f4f5f7] flex items-center justify-between shrink-0">
          <span className="text-[11px] font-mono text-[#5e6c84]">
            AssetTrack TI • Gestão de Ativos e Service Desk
          </span>
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-white hover:bg-[#ebecf0] text-[#172b4d] font-semibold text-xs rounded-xl border border-[#c1d7e9] transition-colors font-mono uppercase shadow-2xs cursor-pointer"
            >
              Fechar
            </button>
            <button
              type="button"
              onClick={handleDownloadClick}
              className="px-4 py-2 bg-[#0c66e4] hover:bg-[#0052cc] text-white font-bold text-xs rounded-xl transition-colors font-mono uppercase shadow-xs flex items-center space-x-1.5 cursor-pointer border-none"
            >
              <Download size={13} className="text-white" />
              <span className="text-white">Baixar APK</span>
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
};
