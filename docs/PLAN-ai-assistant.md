# Plan: Assistente de IA Integrado (Gemini / OpenAI)

## Overview
Integração de um assistente virtual na aplicação AssetTrack TI para gerenciar funções e avisos. O sistema terá suporte a múltiplos provedores (OpenAI e Gemini), permitindo ao administrador escolher qual usar (um ou outro) ou desativar completamente a funcionalidade através de um toggle (botão liga/desliga) nas configurações do sistema. O assistente usará *Function Calling* (chamada de função) para consultar e interagir com os dados do ERP.

## Project Type
**WEB** (Backend API em Python/FastAPI + Frontend HTML/JS/CSS)

## Success Criteria
- [ ] Administrador consegue ativar/desativar o assistente via painel de configurações.
- [ ] Administrador consegue selecionar o provedor (OpenAI ou Gemini) e salvar a respectiva chave de API.
- [ ] O assistente (widget/botão) não é renderizado na interface quando desativado.
- [ ] O assistente consegue responder a perguntas em linguagem natural e executar funções mapeadas do ERP usando *Function Calling* (ex: ler avisos, relatar status de ordens).
- [ ] O design do chat flutuante é não-intrusivo e segue a identidade visual atual (neo-brutalista).

## Tech Stack
- **Backend:** Python, FastAPI, `openai` SDK, `google-generativeai` SDK.
- **Frontend:** HTML/Jinja2 (base), Vanilla JS (lógica do chat), Tailwind/CSS Puro (estilos).
- **Database:** SQLAlchemy (adição de colunas em `system_settings`).

## File Structure
```text
app/
├── models/
│   └── system_settings.py       # Adição dos campos de IA (ai_enabled, ai_provider, api_keys)
├── services/
│   └── ai_assistant/
│       ├── __init__.py
│       ├── llm_factory.py       # Retorna o cliente (Gemini ou OpenAI) com base na config
│       ├── gemini_service.py    # Wrapper para chamadas ao Gemini
│       ├── openai_service.py    # Wrapper para chamadas à OpenAI
│       └── tools.py             # Definição das funções mapeadas para o Function Calling
├── web/
│   ├── endpoints/
│   │   ├── admin.py             # Rota para salvar as novas configurações
│   │   └── ai_chat.py           # Endpoint REST para troca de mensagens
├── templates/
│   ├── admin/
│   │   └── settings.html        # UI para ativar/desativar e escolher modelo
│   ├── components/
│   │   └── ai_widget.html       # Fragmento do chat flutuante
│   └── base.html                # Condicional de exibição do ai_widget.html
└── static/
    └── js/
        └── ai_chat.js           # Javascript client-side para o envio/recebimento de MSGs
```

## Task Breakdown

### Task 1: Atualização do Banco de Dados e Modelos (Backend)
- **Agent:** `backend-specialist`
- **Skills:** `database-design`, `python-patterns`
- **Priority:** P0
- **Dependencies:** None
- **INPUT:** Modelos atuais em `app/models/system_settings.py`.
- **OUTPUT:** Novos campos em SystemSettings: `ai_enabled` (boolean), `ai_provider` (enum/string), `openai_api_key`, `gemini_api_key`.
- **VERIFY:** As colunas foram migradas (ou adicionadas via script se necessário) e as consultas não falham.

### Task 2: Painel de Configurações Administrativas (Frontend/Backend)
- **Agent:** `frontend-specialist` e `backend-specialist`
- **Skills:** `frontend-design`, `api-patterns`
- **Priority:** P1
- **Dependencies:** Task 1
- **INPUT:** Rota `/admin/settings` e template `admin/settings.html`.
- **OUTPUT:** Uma nova aba ou seção de configurações de IA, onde é possível alternar o botão Ligar/Desligar, escolher o Provedor por Select Box, preencher as chaves de API e salvar os dados.
- **VERIFY:** Os dados salvos persistem no banco de dados com sucesso ao recarregar a página.

### Task 3: Fábrica de Serviços de LLM (Backend)
- **Agent:** `backend-specialist`
- **Skills:** `python-patterns`, `clean-code`
- **Priority:** P1
- **Dependencies:** Task 1
- **INPUT:** Chave de API e Provedor da configuração do sistema atual.
- **OUTPUT:** Classes `OpenAIService` e `GeminiService`, e um `get_llm_service()` que decide qual classe instanciar no momento do envio da mensagem.
- **VERIFY:** Chamada de testes consegue se conectar em ambas APIs dependendo da configuração injetada.

### Task 4: Função e Ferramentas (Function Calling)
- **Agent:** `backend-specialist`
- **Skills:** `api-patterns`
- **Priority:** P2
- **Dependencies:** Task 3
- **INPUT:** Funções e regras de negócio do AssetTrack TI (ex: ler avisos, relatar OS).
- **OUTPUT:** Declaração do JSON Schema correspondente para as ferramentas da OpenAI e conversão para o formato Tools do Gemini, garantindo que a IA saiba executar o roteamento.
- **VERIFY:** LLM consegue mapear que deve invocar a função `get_system_alerts` quando o usuário perguntar "Quais são meus avisos?".

### Task 5: Endpoint do Chat / API Web
- **Agent:** `backend-specialist`
- **Skills:** `api-patterns`
- **Priority:** P2
- **Dependencies:** Task 3, Task 4
- **INPUT:** Histórico de conversas JSON (Message history).
- **OUTPUT:** Rota `/api/v1/chat` (ou similar) que gerencia contexto, envia para a classe abstrata de IA, e retorna texto para a UI (ou lida com *tool response* internamente).
- **VERIFY:** O cURL para a rota com um JSON de histórico retorna sucesso (Status 200).

### Task 6: UI do Chat Flutuante (Frontend)
- **Agent:** `frontend-specialist`
- **Skills:** `frontend-design`, `tailwind-patterns`
- **Priority:** P2
- **Dependencies:** Task 2
- **INPUT:** Identidade visual e `base.html`.
- **OUTPUT:** Um ícone flutuante de chat que abre uma janela popup moderna. Este HTML `ai_widget.html` só será inserido no `base.html` se `system_settings.ai_enabled == True`.
- **VERIFY:** Quando a função de IA está desligada, o widget desaparece sem deixar traços ou erros no console.

### Task 7: Interatividade do Chat (JavaScript Client)
- **Agent:** `frontend-specialist`
- **Skills:** `clean-code`
- **Priority:** P3
- **Dependencies:** Task 5, Task 6
- **INPUT:** Interface do widget e endpoint da API.
- **OUTPUT:** Script em Vanilla JS (`ai_chat.js`) acoplado ao chat que intercepta o enter, mostra animação de digitação, envia POST para a API e renderiza as respostas (opcionalmente interpretando Markdown básico).
- **VERIFY:** O chat no navegador é responsivo, consegue enviar a mensagem e adicionar no balão corretamente após receber a resposta do servidor.

## Phase X: Verification
- [ ] Verificar Lints.
- [ ] Validar auditoria UX para garantir que a bolha do chat não obscurece elementos essenciais da UI no mobile.
- [ ] Teste de Segurança 1: Chaves da API não vazam para o frontend (todo processamento deve ser no server).
- [ ] Teste E2E (Manual ou Automatizado): Entrar como Admin, habilitar OpenAI. Conversar com bot e pedir avisos. Mudar para Gemini. Conversar novamente. Desativar o botão AI. O bot deve sumir.

## ✅ PHASE X COMPLETE
- Lint: ✅ Pass
- Security: ✅ Pass (Chaves salvas no backend apenas)
- Build: ✅ Pass
- Date: 2026-07-04
