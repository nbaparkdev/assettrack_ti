# Plan: Implantação do Módulo ERP de Compras (Procurement) Integrado

## 📋 Overview
Este plano descreve o desenvolvimento e a integração de um novo **Módulo de Compras (Procurement)** ao ERP AssetTrack TI. Ele cobrirá todo o ciclo de compras: desde solicitações de compras (com alçadas e controle de orçamento por centro de custo), cotações com comparativos, pedidos de compra, recebimentos físicos (parciais/totais com controle de estoque de uso interno e criação automática de Ativos), contratos com alertas de vencimento, até relatórios gerenciais e auditoria.

O módulo poderá ser ativado/desativado de forma dinâmica pelas configurações do administrador, mantendo o banco de dados preservado.

---

## 🏗️ Project Type
**WEB** (FastAPI + SQLAlchemy + Jinja2 + HTML/Tailwind)

---

## 🎯 Success Criteria
1. **Controle de Módulo (Feature Toggle)**: Ativar/desativar o módulo no painel administrativo preserva os dados, oculta todos os menus/links e bloqueia as rotas de backend e frontend.
2. **Ciclo Completo de Compras**: Fluxo contínuo e integrado: Solicitação (SC) ➔ Aprovação (Multinível/Alçadas com controle de orçamento) ➔ Cotação (CQ) com comparativo automático ➔ Pedido de Compra (PC) ➔ Recebimento (Parcial ou Total) e Contratos.
3. **Integração de Estoque e Ativos**:
   - Criação direta de Ativos patrimoniais a partir do recebimento de compras autorizadas.
   - Controle de saldo físico simples para itens de consumo (ex: lâmpadas, lubrificantes) com baixas integradas ao uso na Manutenção Preventiva/Corretiva.
4. **Integração com Manutenção e Service Desk**:
   - Técnicos podem solicitar compras diretamente de uma Ordem de Serviço ou de um Chamado de Service Desk.
5. **Auditoria e Relatórios**: Trilha de auditoria para cada ação (quem, quando, o quê, IP) e relatórios consolidados em tela com exportação para PDF, Excel e CSV.

---

## 🧰 Tech Stack & Rationale
- **FastAPI / SQLAlchemy AsyncORM**: Alta performance assíncrona para requisições e persistência relacional no PostgreSQL.
- **Jinja2 & Tailwind CSS**: Interfaces limpas, responsivas, neo-brutalistas modernas, totalmente livres de cores roxas/violetas (*Purple Ban*).
- **Pydantic v2**: Validação de dados robusta nos endpoints de API.

---

## 📁 File Structure
```plaintext
app/
├── models/
│   └── procurement.py         # Todos os novos modelos SQLAlchemy (PurchaseRequest, etc.)
├── schemas/
│   └── procurement.py         # Schemas de validação Pydantic
├── crud/
│   └── procurement.py         # Métodos CRUD assíncronos
├── web/
│   ├── dependencies.py        # Dependência para verificar se o módulo de compras está ativo
│   └── endpoints/
│       ├── procurement.py     # Endpoints da Web UI para Compras
│       └── api_procurement.py # Endpoints da REST API Swagger
├── services/
│   └── procurement_service.py # Lógica de negócio (comparativos, criação de ativos, baixa de estoque)
└── templates/
    └── procurement/           # Telas (dashboard, solicitacoes, cotacoes, pedidos, contratos, etc.)
```

---

## 🛠️ Task Breakdown

### Task 1: Criação dos Modelos SQLAlchemy
- **Agent**: `database-architect`
- **Skills**: `database-design`, `clean-code`
- **Priority**: P0
- **Dependencies**: Nenhuma
- **INPUT**: Modelos base e sessão SQLAlchemy.
- **OUTPUT**: Arquivo `app/models/procurement.py` contendo:
  - `PurchaseCategory` e `PurchaseProduct`
  - `CostCenter` (com orçamento mensal/anual e configurações de alerta/bloqueio)
  - `PurchaseRequest` e `PurchaseRequestItem`
  - `PurchaseApproval` (histórico e níveis: Solicitante ➔ Gestor ➔ Gerente ➔ Financeiro ➔ Diretoria ➔ Compras)
  - `PurchaseQuotation`, `PurchaseQuotationSupplier`, `PurchaseQuotationItem`
  - `PurchaseOrder` e `PurchaseOrderItem`
  - `PurchaseReceiving`, `PurchaseReceivingItem`
  - `PurchaseContract`
  - `PurchaseAttachment` (anexos com caminhos de arquivos)
  - `PurchaseHistory` (auditoria)
  - `PurchaseNotification` (mensagens e avisos)
  - `MaterialStock` e `MaterialStockTransaction` (para o estoque simples de consumo)
- **VERIFY**: Importar os modelos em `app/models/__init__.py` para que as migrações/criações ocorram perfeitamente no Docker/PostgreSQL.

### Task 2: Desenvolvimento de Pydantic Schemas e CRUD
- **Agent**: `backend-specialist`
- **Skills**: `python-patterns`, `clean-code`
- **Priority**: P1
- **Dependencies**: Task 1
- **INPUT**: Modelos SQLAlchemy criados.
- **OUTPUT**: Arquivo `app/schemas/procurement.py` e `app/crud/procurement.py`.
- **VERIFY**: Implementação de testes simples ou imports limpos nos testes unitários.

### Task 3: Feature Toggle & Middleware de Bloqueio
- **Agent**: `backend-specialist`
- **Skills**: `api-patterns`, `clean-code`
- **Priority**: P1
- **Dependencies**: Task 2
- **INPUT**: Roteamento do módulo de Compras e `app/web/dependencies.py`.
- **OUTPUT**:
  - Inclusão do toggle `purchases_enabled` na tabela `system_settings` e tela administrativa `modules.html`.
  - Dependência `check_purchases_enabled` para rejeitar/redirecionar requisições para `/compras/*` ou `/api/compras/*` caso desativado.
- **VERIFY**: Tentar acessar rotas com o toggle desligado e certificar redirecionamento seguro para `/assets/`.

### Task 4: Criação dos Serviços e Regras de Negócio (Integrações)
- **Agent**: `backend-specialist`
- **Skills**: `api-patterns`
- **Priority**: P1
- **Dependencies**: Task 2
- **INPUT**: Métodos CRUD de Compras.
- **OUTPUT**: Arquivo `app/services/procurement_service.py` com:
  - Comparativo automático de cotações destacando menor preço, prazo e custo-benefício.
  - Conversão automática de Recebimento de Equipamentos em Ativos (tabela `assets`), herdando fornecedor, nota fiscal, modelo e gerando tag de patrimônio sequencial.
  - Integração com OS da Manutenção (inserção de botão para solicitar compra de peças) e Service Desk.
  - Baixa automática no estoque simples (`MaterialStock`) quando consumido na manutenção.
- **VERIFY**: Validar fluxo de dados logicamente e simular a criação de ativos.

### Task 5: Implementação dos Endpoints REST (API) e Swagger
- **Agent**: `backend-specialist`
- **Skills**: `api-patterns`
- **Priority**: P2
- **Dependencies**: Task 3, Task 4
- **INPUT**: Schemas Pydantic e Services.
- **OUTPUT**: Endpoints CRUD em `app/web/endpoints/api_procurement.py` montados com paginação, filtros por centro de custo, fornecedor e status.
- **VERIFY**: Acessar o Swagger (/docs) e verificar se a API está documentada e responde adequadamente.

### Task 6: Desenvolvimento da Interface Web (Jinja2 + Tailwind CSS)
- **Agent**: `frontend-specialist`
- **Skills**: `frontend-design`
- **Priority**: P2
- **Dependencies**: Task 4, Task 5
- **INPUT**: Rotas web em `app/web/endpoints/procurement.py`.
- **OUTPUT**: Templates na pasta `app/templates/procurement/`:
  - `dashboard.html`: KPIs executivos, gráficos de gastos (TI x Infra), status dos pedidos e tabelas rápidas.
  - `solicitacoes.html`: Formulário de criação de Solicitação de Compra com linha do tempo de aprovação.
  - `cotacoes.html` & `comparativo.html`: Comparativo lado-a-lado elegante das cotações.
  - `pedidos.html`: Emissão e impressão do pedido de compra.
  - `recebimento.html`: Confirmação total ou parcial, drag-and-drop de imagens/notas e envio para estoque/ativos.
  - `contratos.html`: Timeline de vencimentos com marcadores visuais coloridos de 90, 60, 30, 15, 7 dias.
  - `produtos.html` & `centro_custos.html`: Cadastros auxiliares.
  - `relatorios.html`: Filtros avançados com geração e botões para download em PDF/Excel/CSV.
- **VERIFY**: Testar responsividade no desktop, tablet e celular. Garantir zero ocorrências de cores roxas/violetas.

### Task 7: Integração Completa nos Menus e Telas Existentes
- **Agent**: `frontend-specialist`
- **Skills**: `frontend-design`
- **Priority**: P2
- **Dependencies**: Task 6
- **INPUT**: `app/templates/base.html`, `app/templates/preventive_maintenance/*`, e chamados do Service Desk.
- **OUTPUT**:
  - Menu dinâmico em `base.html` sob a seção "Compras" condicionada a `request.state.purchases_enabled`.
  - Inserção de atalho "Solicitar Compra" dentro do visual da Ordem de Serviço de manutenção e do Chamado.
- **VERIFY**: Testar fluxo completo como Administrador (com módulo ativo e inativo).

---

## 🏁 Phase X: Final Verification
- [x] Task 1: Modelos SQLAlchemy — **CONCLUÍDO**
- [x] Task 2: Pydantic Schemas e CRUD — **CONCLUÍDO**
- [x] Task 3: Feature Toggle & Middleware de Bloqueio — **CONCLUÍDO**
- [x] Task 4: Serviços e Regras de Negócio (Comparativo de Cotações, Ativos) — **CONCLUÍDO**
- [x] Task 5: Endpoints REST / Swagger — **CONCLUÍDO**
- [x] Task 6: Interface Web (Jinja2 + Tailwind) — **CONCLUÍDO**
  - Dashboard, Solicitações, Cotações, Pedidos, Recebimento, Contratos, Produtos, Centros de Custo, Relatórios
- [x] Task 7: Integração nos Menus e Telas Existentes — **CONCLUÍDO**
  - Atalho "Solicitar Compra" em OS de Manutenção Preventiva, Solicitações de Manutenção e Chamados Service Desk
  - Formulário pré-preenchido via parâmetros de URL (origem_tipo, origem_id, descricao)
  - Correção da opacidade do dropdown no menu superior (base.html)
- [x] Exportação CSV de Solicitações e Contratos — **CONCLUÍDO**
- [x] Alertas de Vencimento de Contratos no Dashboard Geral — **CONCLUÍDO**
- [x] Status especial "Aguardando Liberação de Orçamento" — **CONCLUÍDO**

---

## ✅ MÓDULO DE COMPRAS COMPLETO

Todas as fases do plano de implantação foram executadas com sucesso.
O módulo cobre o ciclo completo: SC → Aprovação → Cotação → PO → Recebimento → Contratos, com relatórios, exportação CSV, alertas de vencimento, integrações com Manutenção e Service Desk, e controle de orçamento por Centro de Custo.
