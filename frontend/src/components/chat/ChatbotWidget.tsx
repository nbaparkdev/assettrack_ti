import React, { useState, useRef, useEffect } from 'react';
import { Bot, X, Send, Loader2 } from 'lucide-react';
import { sendChatMessage } from '../../api/ai';
import { getFeatureFlags } from '../../api/features';
import type { ChatMessage } from '../../types/ai';

export const ChatbotWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    const refreshVisibility = async () => {
      try {
        const flags = await getFeatureFlags();
        if (active) setEnabled(flags.ai_enabled === true);
      } catch {
        if (active) setEnabled(false);
      }
    };
    const handleVisibilityChange = (event: Event) => {
      const detail = (event as CustomEvent<{ enabled?: boolean }>).detail;
      if (typeof detail?.enabled === 'boolean') setEnabled(detail.enabled);
      void refreshVisibility();
    };
    void refreshVisibility();
    const interval = window.setInterval(refreshVisibility, 30000);
    window.addEventListener('assettrack-ai-visibility-change', handleVisibilityChange);
    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener('assettrack-ai-visibility-change', handleVisibilityChange);
    };
  }, []);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        { role: 'assistant', content: 'Olá! Sou o Assistente IA do Assettrack. Como posso ajudar com os ativos ou solicitações hoje?' }
      ]);
    }
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(newMessages);
      setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
    } catch (error: any) {
      const serverMessage = error?.response?.data?.error;
      const message = serverMessage
        ? `Não foi possível obter uma resposta: ${serverMessage}`
        : 'Desculpe, ocorreu um erro ao se comunicar com o servidor.';
      setMessages(prev => [...prev, { role: 'assistant', content: message }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!enabled) return null;

  return (
    <>
      {/* Botão flutuante */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-20 md:bottom-6 right-4 md:right-6 p-3.5 sm:p-4 bg-[#0c66e4] text-white rounded-full shadow-xl hover:bg-[#0055cc] active:scale-95 transition-all z-40 flex items-center justify-center cursor-pointer"
        title="Assistente IA"
        aria-label="Assistente IA"
      >
        {isOpen ? <X size={22} /> : <Bot size={22} />}
      </button>

      {/* Janela de Chat */}
      {isOpen && (
        <div className="fixed bottom-36 md:bottom-24 right-3 sm:right-6 w-[calc(100vw-1.5rem)] sm:w-96 h-[480px] max-h-[75vh] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden z-50 animate-fade-in">
          {/* Header */}
          <div className="bg-[#0c66e4] text-white p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bot size={22} />
              <div>
                <h3 className="font-semibold text-base leading-tight">Assistente IA</h3>
                <p className="text-blue-100 text-[11px]">Suporte Inteligente</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] rounded-xl p-3 text-sm leading-relaxed ${msg.role === 'user' ? 'bg-[#0c66e4] text-white rounded-br-none' : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'}`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 rounded-xl rounded-bl-none p-3 shadow-sm">
                  <Loader2 className="animate-spin text-[#0c66e4]" size={16} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-3 bg-white border-t border-gray-200 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Digite sua mensagem..."
              className="flex-1 bg-gray-100 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-[#0c66e4] text-sm"
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="p-2.5 bg-[#0c66e4] text-white rounded-lg hover:bg-[#0055cc] active:scale-95 transition-all disabled:opacity-50 cursor-pointer"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
