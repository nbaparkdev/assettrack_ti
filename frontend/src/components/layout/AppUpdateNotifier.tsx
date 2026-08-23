import React, { useEffect, useState } from 'react';
import { Sparkles, Download, X, ArrowRight } from 'lucide-react';
import { appVersionApi, type AppVersionInfo } from '../../api/appVersion';
import { APP_CONFIG } from '../../config/appVersion';
import { ApkDownloadModal } from './ApkDownloadModal';

export const AppUpdateNotifier: React.FC = () => {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [serverVersion, setServerVersion] = useState<AppVersionInfo | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    // Check if dismissed in this session
    const isDismissed = sessionStorage.getItem('assettrack_update_dismissed');
    if (isDismissed) {
      setDismissed(true);
    }

    const checkVersion = async () => {
      try {
        const info = await appVersionApi.getVersion();
        setServerVersion(info);
        if (info && info.version_code > APP_CONFIG.CURRENT_VERSION_CODE) {
          setUpdateAvailable(true);
        }
      } catch (err) {
        // Silent fail for network issues
      }
    };

    checkVersion();
    const interval = setInterval(checkVersion, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    sessionStorage.setItem('assettrack_update_dismissed', 'true');
  };

  if (!updateAvailable || dismissed || !serverVersion) {
    return (
      <ApkDownloadModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    );
  }

  return (
    <>
      <div className="fixed bottom-4 right-4 z-50 max-w-md bg-white border-2 border-[#0c66e4] shadow-2xl rounded-2xl p-4 animate-in slide-in-from-bottom-5 fade-in text-[#172b4d]">
        <div className="flex items-start justify-between gap-3">
          <div className="p-2.5 bg-[#0c66e4]/15 text-[#0c66e4] rounded-xl shrink-0">
            <Sparkles size={20} className="animate-spin" />
          </div>
          <div className="space-y-1 flex-1 text-left">
            <div className="flex items-center space-x-2">
              <h4 className="font-bold text-sm text-[#172b4d] m-0">Nova Versão do App Disponível!</h4>
              <span className="bg-emerald-500 text-white text-[10px] font-bold font-mono px-2 py-0.5 rounded-full shadow-2xs">
                v{serverVersion.version_name}
              </span>
            </div>
            <p className="text-xs text-[#5e6c84] m-0 leading-relaxed font-sans">
              Uma nova versão do <strong>AssetTrack TI Mobile</strong> está pronta para download com melhorias e correções.
            </p>
            <div className="pt-2 flex items-center space-x-2">
              <button
                type="button"
                onClick={() => setModalOpen(true)}
                className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-[#0c66e4] hover:bg-[#0052cc] text-white font-bold text-xs rounded-lg transition-all font-mono uppercase shadow-md shadow-[#0c66e4]/20 border-none cursor-pointer"
              >
                <Download size={13} className="text-white" />
                <span className="text-white">Baixar Atualização</span>
                <ArrowRight size={12} className="text-white" />
              </button>
              <button
                type="button"
                onClick={handleDismiss}
                className="px-2.5 py-1.5 text-[#5e6c84] hover:text-[#172b4d] text-xs rounded-lg font-mono hover:bg-[#ebecf0] transition-colors cursor-pointer border-none bg-transparent"
              >
                Depois
              </button>
            </div>
          </div>
          <button
            type="button"
            onClick={handleDismiss}
            className="text-[#5e6c84] hover:text-[#172b4d] p-1 rounded-lg hover:bg-[#ebecf0] transition-colors cursor-pointer border-none bg-transparent"
            title="Fechar aviso"
          >
            <X size={16} />
          </button>
        </div>
      </div>

      <ApkDownloadModal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
};
