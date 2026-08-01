# Plan: Módulo Projetos Internos (Kanban)

## 📋 Overview
Este plano define a arquitetura, o modelo de dados e os passos de implementação para o novo módulo plugável **"Projetos Internos (Kanban)"** na aplicação Assettrack TI. O módulo permite o gerenciamento visual estilo Trello de projetos e tarefas da empresa, totalmente integrado aos Usuários e ao módulo de Ativos/Patrimônio.

---

## 🏗️ Project Type
**WEB** (FastAPI + AsyncORM SQLAlchemy + Jinja2 + HTMX + Tailwind Industrial)

---

## 🎯 Success Criteria
1. **Feature Toggle Global**: O módulo pode ser ativado/desativado globalmente pelo painel administrativo (`/admin/modulos`) e persistido na tabela `system_settings`.
2. **Visibilidade por Perfil & Projeto (RBAC)**:
   - Perfis `ADMIN`, `TECNICO`, `GERENTE`, `GERENTE_INFRA`, `COMPRAS` e `RH` têm acesso ao módulo quando ativado.
   - Perfil `USUARIO_COMUM` só visualiza a aba/módulo Kanban se for participante ativo em pelo menos um projeto.
3. **Controle Administrativo de Projetos**: Administradores e Criadores do Projeto podem ativar, desativar ou arquivar qualquer projeto individualmente.
4. **Kanban Estilo Trello**:
   - Suporte a colunas personalizáveis por projeto (iniciando com o padrão: *A Fazer*, *Em Andamento*, *Aguardando Compras*, *Concluído*).
   - Movimentação de cards entre colunas (HTMX/Drag-and-drop).
5. **Conteúdo Rico e Vínculos nos Cards**:
   - Descrições em formato Markdown.
   - Upload de imagens e inclusão de links externos.
   - Vínculo com 1 ou mais Ativos do sistema.
   - Atribuição de Criador, Responsável e Múltiplos Participantes.
   - Exibição de avatares/iniciais do Criador e Participantes na capa e modal do card.

---

## 🧰 Tech Stack & Rationale
- **SQLAlchemy AsyncORM**: Modelagem relacional para `KanbanProject`, `KanbanColumn`, `KanbanCard`, `KanbanAttachment` e tabelas N:M para participantes e ativos.
- **FastAPI + Jinja2**: Rotas web com validação de permissões e controle de sessão.
- **HTMX**: Atualizações dinâmicas de cards, movimentação entre colunas e adição de comentários/anexos sem recarregar a página.
- **Markdown / Marked.js**: Renderização elegante de descrições ricas.
- **Tailwind Industrial**: Design neo-brutalista e responsivo mantendo a identidade visual do Assettrack TI.

---

## 📁 File Structure
```plaintext
app/
├── models/
│   └── kanban.py                     # Modelos SQLAlchemy para Projetos, Colunas, Cards e Anexos
├── crud/
│   └── kanban.py                     # Lógica de banco de dados para Projetos e Cards
├── web/
│   ├── dependencies.py                # Dependência `check_kanban_enabled` e validações RBAC
│   └── endpoints/
│       └── kanban.py                 # Rotas FastAPI do módulo Kanban
└── templates/
    ├── kanban/
    │   ├── index.html                # Dashboard de Projetos (Ativos / Arquivados)
    │   ├── project_form.html         # Formulário de Criação/Edição de Projeto
    │   ├── board.html                # Quadro Kanban interativo do projeto
    │   └── partials/
    │       ├── card_modal.html       # Modal de detalhes/edição do Card
    │       └── card_item.html        # Card individual renderizado na coluna
    ├── admin/
    │   └── modules.html              # Atualização do painel de ativação de módulos
    └── base.html                     # Menu de navegação atualizado com o módulo 07_PROJETOS
```

---

## 🛠️ Task Breakdown

### Task 1: Criar Modelos SQLAlchemy (`app/models/kanban.py`)
- **Agent**: `database-architect`
- **Skills**: `database-design`, `clean-code`
- **Priority**: P0
- **Dependencies**: Nenhuma

### Task 2: Implementar CRUD (`app/crud/kanban.py`)
- **Agent**: `backend-specialist`
- **Skills**: `python-patterns`, `clean-code`
- **Priority**: P0
- **Dependencies**: Task 1

### Task 3: Configurar Feature Toggle e Dependências (`app/web/dependencies.py` & `app/main.py`)
- **Agent**: `backend-specialist`
- **Skills**: `api-patterns`
- **Priority**: P1
- **Dependencies**: Task 2

### Task 4: Criar Endpoints FastAPI (`app/web/endpoints/kanban.py`)
- **Agent**: `backend-specialist`
- **Skills**: `api-patterns`, `python-patterns`
- **Priority**: P1
- **Dependencies**: Task 3

### Task 5: Desenvolver Interface e Templates (`app/templates/kanban/*`)
- **Agent**: `frontend-specialist`
- **Skills**: `frontend-design`, `ui-ux-pro-max`
- **Priority**: P2
- **Dependencies**: Task 4

### Task 6: Integrar com Painel Admin & Menu Principal (`admin/modules.html` & `base.html`)
- **Agent**: `frontend-specialist` & `backend-specialist`
- **Skills**: `frontend-design`
- **Priority**: P2
- **Dependencies**: Task 5
