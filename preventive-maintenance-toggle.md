# Plan: Toggle Módulo de Manutenção Preventiva e Corretiva

## 📋 Overview
Este plano define a arquitetura e os passos de implementação para transformar o módulo de **Gestão de Manutenção Preventiva e Corretiva** em um recurso chaveável (*feature toggle*). A ativação/desativação será persistida no banco de dados, e **apenas administradores** terão permissão para alternar esse estado através de um novo gerenciador de módulos no painel administrativo.

---

## 🏗️ Project Type
**WEB** (FastAPI + SQLAlchemy + Jinja2 + HTML/Tailwind)

---

## 🎯 Success Criteria
1. **Persistência Dinâmica**: Estado do módulo salvo em banco de dados (`system_settings`), permitindo alternar instantaneamente sem necessidade de reiniciar a aplicação ou o container Docker.
2. **Controle de Acesso (RBAC)**: Apenas usuários com o papel `ADMIN` podem visualizar a tela de gerenciamento de módulos e alterar o estado da chave.
3. **Redirecionamento Seguro**: Qualquer acesso direto às rotas `/manutencao-preventiva/*` por usuários quando o módulo estiver desativado deve redirecionar automaticamente para a página principal (Dashboard de Ativos `/assets/`).
4. **Navegação Dinâmica**: O link para "Manutenção Preventiva" no menu principal (`base.html`) deve ser ocultado para não-administradores quando o módulo estiver desativado.

---

## 🧰 Tech Stack & Rationale
- **FastAPI Dependencies**: Utilizaremos o mecanismo de injeção de dependências do FastAPI (`Depends`) para verificar o status do módulo antes de executar as rotas de manutenção.
- **SQLAlchemy AsyncORM**: Criação da tabela `system_settings` no modelo de dados para garantir consultas rápidas e escaláveis no PostgreSQL.
- **Jinja2 Templates**: Modificação condicional no `base.html` e criação da tela administrativa `modules.html`.

---

## 📁 File Structure
```plaintext
app/
├── models/
│   └── system_settings.py         # Novo modelo para configurações do sistema
├── crud/
│   └── system_settings.py         # Módulo CRUD para acesso às configurações
├── web/
│   ├── dependencies.py            # Nova dependência para checar status do módulo
│   └── endpoints/
│       ├── preventive_maintenance.py # Inserção da dependência nas rotas
│       └── admin_modules.py       # Novas rotas para gerenciar módulos
└── templates/
    ├── base.html                  # Atualização da barra de navegação
    └── admin/
        └── modules.html           # Novo template para ativar/desativar módulos
```

---

## 🛠️ Task Breakdown

### Task 1: Criar Modelo `SystemSettings`
- **Agent**: `database-architect`
- **Skills**: `database-design`, `clean-code`
- **Priority**: P0
- **Dependencies**: Nenhuma
- **INPUT**: Modelo base do SQLAlchemy (`Base`).
- **OUTPUT**: Arquivo `app/models/system_settings.py` contendo a classe `SystemSettings` (chaves `setting_key` e `setting_value`).
- **VERIFY**: Verificar integridade da declaração e importação no `app/models/__init__.py`.

### Task 2: Criar CRUD de Configurações
- **Agent**: `backend-specialist`
- **Skills**: `python-patterns`, `clean-code`
- **Priority**: P1
- **Dependencies**: Task 1
- **INPUT**: Modelo `SystemSettings`.
- **OUTPUT**: Arquivo `app/crud/system_settings.py` com métodos `get_setting` e `set_setting` (com fallback padrão `preventive_maintenance_enabled = True`).
- **VERIFY**: Importar corretamente em `app/crud/__init__.py`.

### Task 3: Implementar Dependência e Atualizar Rotas de Manutenção
- **Agent**: `backend-specialist`
- **Skills**: `api-patterns`, `clean-code`
- **Priority**: P1
- **Dependencies**: Task 2
- **INPUT**: `app/web/dependencies.py` e `app/web/endpoints/preventive_maintenance.py`.
- **OUTPUT**: Função `check_module_enabled` que consulta o banco e faz `RedirectResponse(url="/assets/")` caso desativado. Adicionar a dependência nas rotas de manutenção.
- **VERIFY**: Acessar rota com chave falsa e confirmar redirecionamento HTTP 307/303.

### Task 4: Criar Tela e Rotas de Gerenciamento de Módulos (Admin)
- **Agent**: `frontend-specialist` & `backend-specialist`
- **Skills**: `frontend-design`, `clean-code`
- **Priority**: P2
- **Dependencies**: Task 2
- **INPUT**: Dependência `get_admin_user_web` (ou validação de papel ADMIN).
- **OUTPUT**: `app/web/endpoints/admin_modules.py` e `app/templates/admin/modules.html` com toggle switch elegante em estilo neo-brutalista (coerente com o sistema).
- **VERIFY**: Testar submissão do formulário de toggle e confirmar atualização no banco.

### Task 5: Atualizar Barra de Navegação (`base.html`)
- **Agent**: `frontend-specialist`
- **Skills**: `frontend-design`
- **Priority**: P2
- **Dependencies**: Task 3, Task 4
- **INPUT**: `app/templates/base.html`.
- **OUTPUT**: Lógica condicional no menu para exibir/ocultar o item "Manutenção Preventiva" e adicionar o link "Módulos" no menu de administração.
- **VERIFY**: Renderizar a interface logado como técnico e verificar ausência do menu quando desativado.

---

## 🏁 Phase X: Final Verification
- [ ] **Lint & Type Check**: Validar código Python com scripts disponíveis.
- [ ] **Security Scan**: Garantir que rotas administrativas exigem permissão de ADMIN.
- [ ] **Database Verification**: Verificar criação da tabela no PostgreSQL via SQLAlchemy.
- [ ] **Design Rules**: Garantir ausência de cores roxas/violetas (Purple Ban) e seguir estilo arquitetural do sistema.
- [ ] **Runtime Test**: Reiniciar container web e validar fluxo completo no navegador.
