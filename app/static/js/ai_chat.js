// ai_chat.js
document.addEventListener('DOMContentLoaded', () => {
    const bubble = document.getElementById('ai-chat-bubble');
    const windowEl = document.getElementById('ai-chat-window');
    const closeBtn = document.getElementById('ai-chat-close-btn');
    const clearBtn = document.getElementById('ai-chat-clear-btn');
    const header = document.getElementById('ai-chat-header');
    const input = document.getElementById('ai-chat-input');
    const sendBtn = document.getElementById('ai-chat-send-btn');
    const messagesContainer = document.getElementById('ai-chat-messages');
    const typingIndicator = document.getElementById('ai-chat-typing');

    const widgetEl = document.getElementById('ai-chat-widget');
    const userEmail = widgetEl ? widgetEl.getAttribute('data-user-email') || 'anonymous' : 'anonymous';
    const userName = widgetEl ? widgetEl.getAttribute('data-user-name') || 'usuário' : 'usuário';
    const userRole = widgetEl ? widgetEl.getAttribute('data-user-role') || 'usuario_comum' : 'usuario_comum';
    const storageKey = `ai_chat_history_${userEmail}`;

    // Keep chat history
    let chatHistory = [];

    // Save history
    const saveHistory = () => {
        try {
            localStorage.setItem(storageKey, JSON.stringify(chatHistory));
        } catch (e) {
            console.error("Failed to save chat history", e);
        }
    };

    // Toggle Window
    const toggleChat = () => {
        if (windowEl.classList.contains('hidden')) {
            windowEl.classList.remove('hidden');
            bubble.classList.add('hidden');
            input.focus();
            localStorage.setItem('ai_chat_open', 'true');
        } else {
            windowEl.classList.add('hidden');
            bubble.classList.remove('hidden');
            localStorage.setItem('ai_chat_open', 'false');
        }
    };

    bubble.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);
    header.addEventListener('click', (e) => {
        if (e.target !== closeBtn && !closeBtn.contains(e.target) && e.target !== clearBtn && !clearBtn.contains(e.target)) {
            toggleChat();
        }
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (confirm("Deseja limpar todo o histórico de conversas com o Assistente?")) {
                chatHistory = [];
                localStorage.removeItem(storageKey);
                sessionStorage.removeItem('ai_welcome_shown');
                renderHistory();
            }
        });
    }

    const appendMessage = (role, text, save = true) => {
        const div = document.createElement('div');
        div.className = 'flex items-start gap-2 ' + (role === 'user' ? 'flex-row-reverse' : '');
        
        let avatar = '';
        let bubbleClass = '';

        if (role === 'user') {
            avatar = `<div class="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white flex-shrink-0 border-2 border-black font-bold text-xs">U</div>`;
            bubbleClass = `bg-blue-100 border-2 border-black p-2 rounded-bl-lg rounded-t-lg rounded-br-none max-w-[85%] shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]`;
        } else {
            avatar = `<div class="w-8 h-8 rounded-full bg-black flex items-center justify-center text-white flex-shrink-0 border-2 border-black">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
                      </div>`;
            bubbleClass = `bg-white border-2 border-black p-2 rounded-br-lg rounded-t-lg rounded-bl-none max-w-[85%] shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] whitespace-pre-wrap`;
        }

        // Basic Markdown replacement for bold and lists
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n- (.*?)/g, '<br>• $1');

        div.innerHTML = `
            ${avatar}
            <div class="${bubbleClass}">
                ${formattedText}
            </div>
        `;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        if (save) {
            chatHistory.push({ role, content: text });
            saveHistory();
        }
    };

    const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;

        // Add user message to UI and history
        appendMessage('user', text);
        input.value = '';

        // Show typing
        typingIndicator.classList.remove('hidden');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        try {
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ messages: chatHistory })
            });

            if (!response.ok) {
                throw new Error('Erro na comunicação com a API');
            }

            const data = await response.json();
            const aiText = data.response;

            // Add AI response to UI and history
            appendMessage('assistant', aiText);

        } catch (error) {
            console.error(error);
            appendMessage('assistant', '⚠️ Desculpe, ocorreu um erro de conexão.');
        } finally {
            typingIndicator.classList.add('hidden');
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    const fetchWelcomeOverview = async () => {
        typingIndicator.classList.remove('hidden');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        try {
            chatHistory.push({ role: 'user', content: 'Me dê um resumo geral do sistema agora: chamados, ativos e manutenções.' });
            saveHistory();
            
            const response = await fetch('/api/v1/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ messages: chatHistory })
            });
            
            if (response.ok) {
                const data = await response.json();
                appendMessage('assistant', data.response);
                chatHistory.push({ role: 'assistant', content: data.response });
                saveHistory();
            } else {
                appendMessage('assistant', 'Não consegui buscar o panorama agora. Me pergunte qualquer coisa!');
            }
        } catch (err) {
            appendMessage('assistant', 'Estou pronto para ajudar! Me pergunte sobre chamados, ativos ou manutenções.');
        } finally {
            typingIndicator.classList.add('hidden');
        }
    };

    const renderHistory = () => {
        messagesContainer.innerHTML = '';
        if (chatHistory.length === 0) {
            const isManager = ['admin', 'gerente_ti', 'gerente_infra'].includes(userRole);
            if (isManager) {
                const greetingText = `Olá, **${userName}**! 👋 Bem-vindo ao AssetTrack. Deixa eu buscar o panorama atual do sistema para você...`;
                appendMessage('assistant', greetingText);
                fetchWelcomeOverview();
            } else {
                const greetingText = `Olá, **${userName}**! Sou o seu Assistente Virtual. 👋\n\nEstou aqui para te ajudar a navegar e utilizar todo o sistema. Se tiver qualquer dúvida de como fazer algo, pode me perguntar! Posso ajudar você a:\n\n• Consultar seus ativos sob sua guarda\n• Criar e acompanhar chamados de suporte (Service Desk)\n• Solicitar manutenções de equipamentos\n• Utilizar seu QR Code pessoal (Crachá Digital) para login rápido\n• Consultar o Manual do Usuário para qualquer dúvida sobre a aplicação\n\nComo posso te ajudar hoje?`;
                appendMessage('assistant', greetingText);
            }
        } else {
            chatHistory.forEach(msg => {
                appendMessage(msg.role, msg.content, false);
            });
        }
    };

    // Load stored history
    try {
        const stored = localStorage.getItem(storageKey);
        if (stored) {
            chatHistory = JSON.parse(stored);
        }
    } catch (e) {
        console.error("Failed to load chat history", e);
    }

    // Render loaded history (or welcome message)
    renderHistory();

    // Toggle Chat window if it was left open in previous page
    if (localStorage.getItem('ai_chat_open') === 'true') {
        windowEl.classList.remove('hidden');
        bubble.classList.add('hidden');
        input.focus();
    } else {
        // Auto-open welcome logic (only once per session if not already conversing)
        if (chatHistory.length === 0 && !sessionStorage.getItem('ai_welcome_shown')) {
            setTimeout(() => {
                toggleChat();
                sessionStorage.setItem('ai_welcome_shown', 'true');
            }, 1500);
        }
    }
});
