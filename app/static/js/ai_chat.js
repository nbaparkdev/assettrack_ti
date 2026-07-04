// ai_chat.js
document.addEventListener('DOMContentLoaded', () => {
    const bubble = document.getElementById('ai-chat-bubble');
    const windowEl = document.getElementById('ai-chat-window');
    const closeBtn = document.getElementById('ai-chat-close-btn');
    const header = document.getElementById('ai-chat-header');
    const input = document.getElementById('ai-chat-input');
    const sendBtn = document.getElementById('ai-chat-send-btn');
    const messagesContainer = document.getElementById('ai-chat-messages');
    const typingIndicator = document.getElementById('ai-chat-typing');

    // Keep chat history in memory for context
    let chatHistory = [];

    // Toggle Window
    const toggleChat = () => {
        if (windowEl.classList.contains('hidden')) {
            windowEl.classList.remove('hidden');
            bubble.classList.add('hidden');
            input.focus();
        } else {
            windowEl.classList.add('hidden');
            bubble.classList.remove('hidden');
        }
    };

    bubble.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);
    header.addEventListener('click', (e) => {
        if (e.target !== closeBtn && !closeBtn.contains(e.target)) {
            toggleChat();
        }
    });

    const appendMessage = (role, text) => {
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
    };

    const sendMessage = async () => {
        const text = input.value.trim();
        if (!text) return;

        // Add user message to UI and history
        appendMessage('user', text);
        chatHistory.push({ role: 'user', content: text });
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
            chatHistory.push({ role: 'assistant', content: aiText });

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
});
