import React, { useEffect, useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAuthStore } from '../../stores/authStore';
import { Navigate } from 'react-router-dom';
import { ChatbotWidget } from '../chat/ChatbotWidget';
import { EmergencyGlobalHandler } from '../emergency/EmergencyGlobalHandler';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { token, loading } = useAuthStore();
  const [showChatbotWidget, setShowChatbotWidget] = useState(() => localStorage.getItem('assettrack-ai-enabled') !== 'false');

  useEffect(() => {
    const handleVisibilityChange = (event: Event) => {
      const detail = (event as CustomEvent<{ enabled?: boolean }>).detail;
      const enabled = detail?.enabled ?? localStorage.getItem('assettrack-ai-enabled') !== 'false';
      setShowChatbotWidget(enabled);
    };

    window.addEventListener('assettrack-ai-visibility-change', handleVisibilityChange as EventListener);
    return () => window.removeEventListener('assettrack-ai-visibility-change', handleVisibilityChange as EventListener);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-brand-dark flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-2 border-brand-primary border-t-transparent animate-spin" />
          <p className="font-mono text-brand-primary text-xs uppercase tracking-widest">
            Autenticando...
          </p>
        </div>
      </div>
    );
  }

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-shell min-h-screen flex text-brand-text">
      <Sidebar />
      <div className="flex-1 flex min-w-0 flex-col h-screen overflow-hidden">
        <Header />
        <main className="app-content flex-1 overflow-y-auto p-6 lg:p-8">
          {children}
          <footer className="mt-10 border-t border-white/25 pt-4 pb-1 text-center text-sm text-[#172b4d]/60">
            © {new Date().getFullYear()} AssetTrack TI. Todos os direitos reservados.
          </footer>
        </main>
        {showChatbotWidget && <ChatbotWidget />}
        <EmergencyGlobalHandler />
      </div>
    </div>
  );
};
