# AssetTrack TI - Documentação de Entrega e Migração

> Documento histórico da migração concluída em 17/08/2026. Use este arquivo como registro da transição arquitetural, não como referência operacional de rotas ou telas atuais.

**Data:** 17 de Agosto de 2026
**De:** Python (FastAPI + Jinja2)
**Para:** Go (Gin + GORM) e React (Vite + TypeScript + Tailwind)

## 📌 Visão Geral

Este documento detalha todos os módulos arquitetados e entregues durante a reescrita do sistema AssetTrack TI. A arquitetura Monorepo agora separa claramente o Backend de Alta Performance (Go) do Frontend Dinâmico (React).

---

## 🚀 Módulos Portados e Aprimorados

### 1. Autenticação e Segurança (Auth & Users)
- **Login Convencional e via QR Code**: Transição completa do login utilizando JWT. O sistema suporta login por e-mail/senha ou leitura de QR Code + PIN para técnicos de campo.
- **Gestão de Usuários e Perfis**: CRUD completo com suporte a níveis de acesso escalonados (Admin, Gerente de TI, Técnico, RH, Comprador, Usuário Comum).
- **Módulo de Perfil Pessoal**:
  - Alteração autônoma de senha com re-autenticação forçada.
  - Upload de Avatar com **compressão client-side em React (Canvas)**, poupando tráfego do servidor.

### 2. Ativos, Inventário e Categorias
- Gestão centralizada de equipamentos (`Asset`) e suas categorias.
- Implementação da **Duplicação em Lote**, facilitando o cadastro rápido de múltiplos computadores/monitores idênticos.
- Impressão de Etiquetas QR em massa no Frontend.

### 3. Service Desk e Help Desk
- Abertura, delegação e resolução de Chamados (Tickets).
- Sistema de interações integrado, registrando o histórico entre técnicos e solicitantes.
- Suporte a upload de evidências (fotos/erros).

### 4. Manutenção (Corretiva e Preventiva)
- **Manutenção Corretiva**: Controle de OS (Ordem de Serviço), apontamento de horas, uso de peças e fotos do conserto.
- **Manutenção Preventiva Automática**:
  - Planos programados por tempo (ex: Semestral).
  - Checklists dinâmicos por categoria de equipamento.
  - Job assíncrono no Go que gera Ordens de Serviço baseadas na expiração do plano.

### 5. Kanban e Gestão Ágil
- Board dinâmico em React (drag-and-drop) para projetos da TI.
- Integração de Server-Sent Events (SSE) para atualização em tempo real de movimentações entre os membros da equipe.
- Cartões com anexos, labels e responsáveis.

### 6. Compras, Fornecedores e Licitações (Procurement)
- Fluxo de compra rigoroso: `Solicitação -> Cotação -> Ordem de Compra -> Recebimento Físico`.
- Gestão de Fornecedores, incluindo upload de arquivos XML e Notas Fiscais com leitura nativa.
- Controle de Almoxarifado e Estoque Mínimo.

### 7. Empréstimos e Termos de Responsabilidade
- Transferência temporária ou definitiva de equipamentos.
- **Geração Client-Side de PDF**: Utilizando `jsPDF`, o frontend gera termos assináveis contendo logos e dados sem onerar a CPU do backend.

### 8. Portal RH e Desligamento (Offboarding)
- Endpoint dedicado para RH desativar funcionários de forma segura.
- O desligamento bloqueia o acesso do usuário instantaneamente e transfere todos os seus equipamentos para o status de "Em Revisão/Manutenção", alertando a TI para recolha e formatação.

### 9. Administração Avançada (Webhooks & Alertas)
- **Emergency Alerts**: Disparo de pânico/alertas globais no topo de todas as telas dos usuários.
- **Webhooks Dispatcher**:
  - Arquitetura baseada em Goroutines para disparos HTTP assíncronos não-bloqueantes.
  - Segurança via assinatura HMAC SHA-256 (`X-Hub-Signature`).
  - Suporta eventos críticos como `ASSET_CREATED`, permitindo integração fácil com Slack, Discord e plataformas n8n.

### 10. Infraestrutura: Backup e Restauração
- Módulo de exportação a quente via `pg_dump` acionado diretamente pela UI.
- Agrupamento inteligente do `database.sql` e todos os arquivos da pasta `/uploads` em um arquivo ZIP unificado.
- Restauração controlada com validação para recuperar instâncias do AssetTrack em segundos.

---

## 🛠️ Tecnologias Finais Empregadas
- **Backend**: Go (Golang) 1.21+, Gin Web Framework, GORM (ORM), PostgreSQL Driver.
- **Frontend**: React 18+, Vite, TypeScript, Zustand (State Management), Tailwind CSS v4, Lucide React (Ícones).
- **Banco e Cache**: PostgreSQL 15, Redis 7 (Rate Limiting).
- **Deployment**: Docker e Docker Compose totalmente configurados.

---

## 📈 Fase 4: Business Intelligence (Dashboards e Relatórios)
Com o núcleo transacional concluído, o sistema agora conta com um poderoso módulo de BI integrado na tela inicial:
- **Painel Executivo em Tempo Real**: Métricas calculadas na base de dados (`SUM`, `COUNT`) via endpoints Otimizados em Go para garantir consumo mínimo de rede.
- **Gráficos Dinâmicos**: Utilização do `Chart.js` via React para desenhar visões agregadas de chamados e saúde de ativos.
- **Exportação de Documentos via Client-Side**: Botão de exportação em PDF dos relatórios gerenciais, renderizados internamente no navegador do administrador via `jsPDF`, eliminando processamento do backend.

---

## 📺 Atualização operacional — 26/08/2026

Foi entregue uma central de manual visual e uma sala de monitoramento preparada para TV:

- Rota `/manual` com landing page técnica, ilustrações, atalhos e conteúdo separado por perfil.
- Rota `/monitoramento` com logo centralizada, modo tela cheia, relógio, conexão ao vivo e indicadores operacionais.
- Atualização automática dos chamados, incluindo status e técnico/responsável atribuído, a cada 5 segundos.
- Inclusão de solicitações de ativos pendentes ou aprovadas aguardando entrega.
- Reutilização do modal emergencial global no monitoramento.
- Som `notificacao_alerta.mp3` para emergências e novidades operacionais.
- Correção da identificação de equipamentos em uso vinculados ao usuário e enriquecimento de alertas legados.
- APK recompilável pelo script `scripts/publish_mobile_apk.sh`, com os assets e telas mais recentes.

---
