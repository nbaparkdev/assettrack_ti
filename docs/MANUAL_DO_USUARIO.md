# 📘 Manual do Usuário - AssetTrack TI

Bem-vindo ao manual do **AssetTrack TI**. Este guia ajudará você a navegar pelas principais funcionalidades do sistema.

---

## 🔐 1. Acesso ao Sistema

### Login Tradicional
Utilize seu email e senha cadastrados para acessar o dashboard principal.

### Login via QR Code (Crachá Digital)
1. Acesse a tela de login QR.
2. Escaneie seu QR Code pessoal (disponível em "Meu QR Code").
3. Digite seu PIN de segurança.

---

## 📊 2. Gestão de Ativos (E-Patrimônio)

### Consultar Equipamentos
No menu **Ativos**, você pode buscar por nome, modelo ou o número de **E-Patrimônio**.
- **E-Patrimônio:** É o número de identificação interna do ativo.
- **Número de Série:** É o serial original do fabricante.

### Scanner de Ativos
Utilize a câmera do seu celular para escanear a etiqueta de um ativo. Isso abrirá instantaneamente a ficha do equipamento com todo o seu histórico.

---

## 🛠️ 3. Solicitação de Manutenção

Se o seu equipamento apresentar defeito:
1. Vá em **Solicitar Manutenção**.
2. Selecione o ativo sob sua responsabilidade.
3. Descreva o problema e envie.
4. Quando o técnico concluir o reparo, você será notificado para confirmar o recebimento.

---

## 🎧 4. Service Desk (Chamados e Suporte)

Para solicitações de suporte que não envolvem reparo físico de hardware (ex: configuração de software, acessos, redes):

### Abertura de Novo Chamado
1. Acesse o menu **Service Desk**.
2. Clique em **Novo Chamado**.
3. Selecione o serviço, defina o nível de prioridade e descreva a solicitação.
4. **Anexo de Imagem (Opcional):** Você pode anexar um print ou foto do erro para facilitar o diagnóstico da equipe de TI.
5. Ao criar, o sistema gerará um código profissional estruturado único (Ex: `CH-2026-0001`).

### Acompanhamento e Timeline de Interações
* O chamado exibe um **histórico cronológico interativo** (Timeline).
* Tanto os usuários solicitantes quanto a equipe técnica podem enviar mensagens de texto e **anexar imagens complementares** (evidências físicas ou prints) no decorrer do atendimento.
* No topo do chamado, é exibido um **QR Code individual**. Aponte a câmera do seu smartphone para o QR Code para acessar o link direto do chamado de forma ágil (`/servicos/chamado/CH-2026-0001`).

### Painel Gerencial (Apenas Administradores e Gerentes)
* Administradores e Gerentes contam com um **Dashboard Gerencial Analítico** moderno no topo da página.
* O painel apresenta **gráficos dinâmicos (ApexCharts)** da distribuição dos chamados por estágio, prioridades, principais categorias e ranking de usuários atendidos.
* **Filtros Avançados:** Posicionados de forma inteligente logo abaixo dos gráficos, permitem pesquisar e filtrar a lista de chamados instantaneamente por código, categoria, status, prioridade e intervalo de datas.

---

## 🚨 5. Chamados de Emergência (Alerta Crítico em Tempo Real)

Para incidentes de extrema gravidade em equipamentos ou infraestrutura que exigem parada total ou risco iminente:

### Como Acionar (Usuários Comuns):
1. No seu **Dashboard principal**, clique no botão vermelho **🚨 ACIONAR EMERGÊNCIA**.
2. No modal que se abrirá, confirme o setor e equipamento afetado (se houver).
3. Descreva brevemente o motivo da emergência e clique em **TRANSMITIR ALERTA EMERGENCIAIS**.
4. O chamado é enviado instantaneamente em tempo real para toda a equipe de TI.

### Como Atender e Acompanhar (Equipe Técnica e Gestores):
1. Quando uma emergência é acionada, um **alerta sonoro** é emitido no navegador e um modal popup vermelho aparece na tela.
2. No topo do seu Dashboard, um **Banner Vermelho** exibirá os contadores em tempo real (`Total Recebidos` e `Pendentes`).
3. Clique em **`[ 📋 VER HISTÓRICO DE ALERTAS ]`** para abrir a central de histórico de emergências.
4. Utilize os filtros (*Todos*, *Pendentes*, *Atendidos*) e clique em **`✓ Marcar Atendido`** para assumir e concluir o atendimento. O sistema registrará seu nome e horário no histórico.

---

## 📱 6. Meu QR Code

Seu **Crachá Digital** serve para:
- Identificação rápida perante a equipe de TI.
- Login sem senha (usando apenas o PIN).
- Validação de recebimento de equipamentos.

> **Dica:** Você pode regenerar seu token QR a qualquer momento caso sinta que a segurança foi comprometida.

---

## 📂 7. Categorias de Ativos

Os administradores podem organizar os ativos em categorias customizáveis para facilitar a gestão.

1. Acesse **Ativos > Categorias** (apenas Admin/Gerente).
2. Cadastre categorias como Notebook, Monitor, Switch, etc.
3. Ao cadastrar ou editar um ativo, selecione a categoria correspondente.

---

## 📊 8. Relatórios de Ativos

O sistema oferece relatórios gerenciais com filtros avançados.

1. Acesse o menu **Ativos & Inventário**.
2. Utilize o painel **Filtros & Relatórios** na própria página.
3. Filtre por data de aquisição, categoria, fornecedor, localização, nota fiscal ou E-Patrimônio.
4. Exporte o resultado atual para **CSV** quando necessário.

---

## 🏢 9. Fornecedores

Mantenha o cadastro de fornecedores organizado e vinculado aos ativos.

1. Acesse o menu **Fornecedores** (Admin/Gerente).
2. Cadastre dados como CNPJ, contato, telefone e endereço.
3. **Auto-preenchimento via NF-e:** Faça upload de um arquivo XML de Nota Fiscal e o sistema preencherá automaticamente os campos do fornecedor.
4. Visualize o histórico de notas fiscais vinculadas a cada fornecedor.

---

## 👥 10. Perfis de Acesso

- **USUARIO:** Consulta seus ativos sob sua guarda, abre chamados de suporte e solicita manutenções.
- **TECNICO:** Atende chamados no Service Desk, gerencia ordens de manutenção e realiza a entrega/devolução física de ativos via scanner QR.
- **COMPRADOR:** Perfil focado em suprimentos. Realiza cotações, emite Pedidos de Compra (PO), gerencia fornecedores e faz o recebimento físico/estoque.
- **RH:** Perfil administrativo simplificado focado na emissão e gestão de aceite de Termos de Responsabilidade para os ativos entregues.
- **GERENTE_TI:** Aprova solicitações de ativos, gerencia o inventário técnico e administra usuários.
- **GERENTE_INFRA:** Gestão do inventário geral de infraestrutura, contratos de fornecedores e categorias.
- **ADMIN:** Controle absoluto e irrestrito sobre todas as configurações do sistema (System Owner).

---

## 🛒 11. Módulo de Compras (Procurement)

O ciclo de compras no sistema é completamente integrado e segue o fluxo abaixo:

1. **Solicitação de Compra (SC):** Qualquer usuário ou técnico pode abrir uma requisição de compra (inclusive como atalho direto dentro de um Chamado ou Ordem de Serviço).
2. **Aprovação de Orçamento:** O gestor ou administrador analisa a solicitação comparando-a com o orçamento do Centro de Custo definido.
3. **Cotação de Preços:** O comprador lança os valores cotados com diferentes fornecedores. O sistema gera automaticamente um comparativo de preços detalhado.
4. **Pedido de Compra (PO):** Após a seleção do vencedor, é gerado um Pedido de Compra estruturado (formato PDF) para envio ao fornecedor.
5. **Recebimento de Itens:** Ao receber a mercadoria, o Almoxarifado realiza o recebimento no sistema (parcial ou total). Itens de consumo entram no estoque de manutenção, enquanto equipamentos geram automaticamente um Ativo patrimonial no inventário de TI.
6. **Contratos:** O menu **Contratos** permite gerenciar a vigência de contratos com fornecedores, exibindo alertas visuais de vencimento a partir de 90 dias.

---

## 🎛️ 12. Configurações de Módulos e Acessos por Menu (RBAC)

Os administradores têm controle total sobre as seções de menu da aplicação através da tela **Configurações**:

1. Acesse **Configurações** no menu lateral ou a rota `/configuracoes`.
2. **Ativar/Desativar Módulos Globais:** Você pode ligar ou desligar funcionalidades inteiras, como Compras e Manutenção Preventiva.
3. **Permissões administrativas:** As alterações são persistidas pela API administrativa e refletidas no frontend conforme o perfil do usuário.
4. Clique em **Salvar Configurações** para aplicar as mudanças.
5. O perfil de administrador continua protegido para evitar bloqueio acidental do sistema.

---

## 🤝 13. Recursos Humanos (RH) e Termos de Responsabilidade

Para controle legal, o sistema oferece um módulo dedicado à emissão de **Termos de Responsabilidade**.

1. **Emissão (RH):** No menu **Recursos Humanos > Termos RH**, visualize as solicitações de entrega de ativos e emita o documento gerado automaticamente.
2. **Assinatura e Controle:** O colaborador assina o documento.
3. **Armazenamento Seguro:** O usuário de RH faz o upload do arquivo digitalizado (PDF ou Imagem) e altera o status para "Assinado", garantindo o histórico digital do aceite.
4. **Simplificação de Tela:** Usuários com o perfil `RH` acessam uma interface enxuta e objetiva, focando na sua atividade principal sem a complexidade dos módulos de Tecnologia da Informação.
