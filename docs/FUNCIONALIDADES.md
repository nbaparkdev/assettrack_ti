# AssetTrack TI - Funcionalidades

> Sistema de Gerenciamento de Ativos de TI com interface web moderna e suporte a Docker.

---

## 🔐 Autenticação & Usuários

| Funcionalidade | Descrição |
|----------------|-----------|
| **Login Tradicional** | Autenticação com email/senha e JWT. |
| **Login via QR** | Autenticação rápida com Crachá Digital + PIN. |
| **Meu QR Code** | Cada usuário possui um QR Code único para identificação e login. |
| **Níveis de Acesso** | `ADMIN`, `GERENTE_TI`, `GERENTE_INFRA`, `TECNICO`, `RH`, `USUARIO`. |

---

## 📦 Gestão de Ativos (E-Patrimônio)

O sistema utiliza o conceito de **E-Patrimônio** para identificação única dos ativos.

| Funcionalidade | Descrição |
|----------------|-----------|
| **Inventário** | Listagem completa com filtros por status, setor e localização. |
| **E-Patrimônio** | Identificador principal único (ex: EP-0001). |
| **Número de Série** | Registro do Serial Number do fabricante para rastreabilidade. |
| **Scanner QR** | Leitura instantânea de etiquetas para abrir detalhes do ativo. |
| **Movimentações** | Histórico completo de quem usou o ativo e por onde ele passou. |
| **Baixa de Ativos** | Registro de saída definitiva do inventário. |
| **Categorias de Ativos** | Organização por categorias customizáveis (ex: Notebook, Monitor, Switch). |
| **Relatórios** | Filtros avançados por data, categoria, fornecedor, NF-e e exportação em PDF. |

---
## 🏢 Fornecedores

| Funcionalidade | Descrição |
|----------------|-----------|
| **Cadastro** | Registro completo de fornecedores com CNPJ, contato e endereço. |
| **Upload NF-e XML** | Upload de arquivo XML de Nota Fiscal para auto-preenchimento dos dados do fornecedor. |
| **Histórico de Notas** | Visualização das notas fiscais vinculadas a cada fornecedor. |

---

## 🎧 Service Desk (Help Desk)

Módulo integrado e profissional de suporte técnico para agilização operacional.

- **Abertura de Chamados:** Solicitação rápida por categorias e setores com suporte opcional a uploads de imagem para identificação visual inicial.
- **Timeline de Interações com Fotos:** Histórico dinâmico cronológico em formato de linha do tempo com suporte a envio de imagens/fotos por usuários e técnicos para evidenciar o andamento.
- **Dashboard Gerencial Premium:** Gráficos interativos (ApexCharts) com análise de status, prioridade de urgência, distribuição de categorias e ranking de usuários (exclusivo para Admins e Gerentes).
- **Filtros Inteligentes de Pesquisa:** Painel de filtros avançados estrategicamente posicionado abaixo dos gráficos para buscas por texto, status, categoria, prioridade e intervalo de datas.
- **Código e QR Rastreável:** Geração de códigos em formato estruturado (ex: `CH-2026-0001`) associados a um QR Code individual de visualização rápida no topo do chamado.
- **Fuso Horário Local (America/Sao_Paulo):** Registro rigoroso de abertura e atualizações no horário do servidor local.
- **Upload de Imagens via Clipboard:** Suporte a colar imagens diretamente do clipboard (Ctrl+V) nos formulários de chamados.

---

## 🛠️ Manutenção

- **Solicitação de Reparo:** Usuários podem relatar defeitos em seus equipamentos.
- **Painel Técnico:** Gestão de filas de conserto e troca de peças.
- **Validação de Entrega:** Uso do QR Code do usuário para confirmar a devolução do item reparado.

---

## 🛒 Compras & Suprimentos (Procurement)

Módulo completo integrado de suprimentos cobrindo do pedido ao recebimento.

- **Fluxo Ponta a Ponta:** Emissão de Solicitações de Compra (SC), aprovação por alçadas de diretoria/financeiro e controle orçamentário por Centro de Custo.
- **Cotações Multilateral:** Lançamento de cotações de fornecedores com painel comparativo do menor preço e melhor custo-benefício.
- **Pedidos de Compra (PO):** Emissão de pedidos formais de compra e monitoramento de entrega.
- **Recebimento e Integração Patrimonial:** A entrada de itens físicos atualiza o estoque simples e cadastra automaticamente novos Ativos no inventário de TI.
- **Gestão de Contratos:** Controle de prazos de validade com alertas visuais no painel geral, opções completas de edição/exclusão de registros, e armazenamento de PDFs de contratos e termos de garantia.

---

## 🤝 Recursos Humanos (RH) e Termos de Responsabilidade

Módulo desenhado para fechar o ciclo de entrega de equipamentos, oferecendo respaldo legal.

- **Fluxo Simplificado:** Usuários do perfil `RH` têm acesso a uma interface amigável (similar à do usuário comum), isolando a complexidade dos módulos técnicos da TI.
- **Emissão Automática:** Geração instantânea de Termos de Responsabilidade em PDF a partir de tickets e solicitações concluídas de entrega de ativos.
- **Gestão de Assinaturas:** Controle visual do status dos termos (Pendente de Assinatura vs. Assinado).
- **Armazenamento de Comprovantes:** Upload de arquivos PDF ou imagens do documento físico assinado pelo colaborador, mantendo tudo centralizado.

---

## 🤖 Assistente de Inteligência Artificial (IA)

Módulo de assistente virtual cognitivo integrado nativamente ao ERP, operando via *Function Calling* para consultar e analisar dados reais do banco de dados de forma conversacional.

- **Provedores Universais:** Suporte integrado a múltiplos ecossistemas de LLM (OpenAI, Gemini, Groq, OpenRouter e Moonshot/Kimi).
- **Gerenciamento de Funcionalidades:** O administrador pode plugar chaves de API, alternar modelos instantaneamente sem reiniciar o servidor e desligar o chat através do painel Administrativo.
- **Acesso ao Banco de Dados (Tool Calling):** O bot tem permissão de leitura programática (Functions) sobre: Inventário de Ativos, Service Desk (Tickets), Manutenções Preventivas e Módulo de Compras (Procurement).
- **Interface Neo-Brutalista:** Widget global, rápido e persistente no canto inferior com feedback visual em animações (ping/radar).

---

## 🎛️ Controle de Módulos e Acessos (RBAC Dinâmico)

- **Feature Toggles:** Ativação ou desativação em tempo real dos módulos de Compras e Manutenção Preventiva.
- **Matriz de Permissões de Menu:** Painel visual que permite ao administrador customizar quais perfis de acesso visualizam cada seção de menu no sistema.
- **Trava de Segurança:** Acesso irrestrito do Administrador é mantido de forma nativa para evitar bloqueios acidentais.

---

## 🎨 Design System: Industrial Technical

- Interface limpa e objetiva com navegação estruturada em módulos e sub-menus organizados (Dropdowns), maximizando o espaço útil da tela e garantindo a padronização.
- Bordas retas e sombras sólidas (Estilo Neo-Brutalism / Industrial).
- Tipografia técnica otimizada para leitura de dados.
- Totalmente responsivo para uso em tablets e smartphones.

---

## 🔧 Stack Tecnológica

- **Backend:** FastAPI (Python 3.12).
- **Frontend:** Jinja2 + Tailwind CSS.
- **Banco de Dados:** PostgreSQL (Dockerizado).
- **Infra:** Docker & Docker Compose.
