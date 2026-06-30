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

## 📱 5. Meu QR Code

Seu **Crachá Digital** serve para:
- Identificação rápida perante a equipe de TI.
- Login sem senha (usando apenas o PIN).
- Validação de recebimento de equipamentos.

> **Dica:** Você pode regenerar seu token QR a qualquer momento caso sinta que a segurança foi comprometida.

---

## 📂 6. Categorias de Ativos

Os administradores podem organizar os ativos em categorias customizáveis para facilitar a gestão.

1. Acesse **Ativos > Categorias** (apenas Admin/Gerente).
2. Cadastre categorias como Notebook, Monitor, Switch, etc.
3. Ao cadastrar ou editar um ativo, selecione a categoria correspondente.

---

## 📊 7. Relatórios de Ativos

O sistema oferece relatórios gerenciais com filtros avançados.

1. Acesse **Ativos > Relatórios**.
2. Utilize os filtros por data de aquisição, categoria, fornecedor, NF-e ou E-Patrimônio.
3. Visualize os resultados na tela ou exporte para **PDF** com um clique.

---

## 🏢 8. Fornecedores

Mantenha o cadastro de fornecedores organizado e vinculado aos ativos.

1. Acesse o menu **Fornecedores** (Admin/Gerente).
2. Cadastre dados como CNPJ, contato, telefone e endereço.
3. **Auto-preenchimento via NF-e:** Faça upload de um arquivo XML de Nota Fiscal e o sistema preencherá automaticamente os campos do fornecedor.
4. Visualize o histórico de notas fiscais vinculadas a cada fornecedor.

---

## 👥 9. Perfis de Acesso

- **USUARIO:** Consulta seus ativos sob sua guarda, abre chamados de suporte e solicita manutenções.
- **TECNICO:** Atende chamados no Service Desk, gerencia ordens de manutenção e realiza a entrega/devolução física de ativos via scanner QR.
- **COMPRADOR:** Perfil focado em suprimentos. Realiza cotações, emite Pedidos de Compra (PO), gerencia fornecedores e faz o recebimento físico/estoque.
- **GERENTE_TI:** Aprova solicitações de ativos, gerencia o inventário técnico e administra usuários.
- **GERENTE_INFRA:** Gestão do inventário geral de infraestrutura, contratos de fornecedores e categorias.
- **ADMIN:** Controle absoluto e irrestrito sobre todas as configurações do sistema (System Owner).

---

## 🛒 10. Módulo de Compras (Procurement)

O ciclo de compras no sistema é completamente integrado e segue o fluxo abaixo:

1. **Solicitação de Compra (SC):** Qualquer usuário ou técnico pode abrir uma requisição de compra (inclusive como atalho direto dentro de um Chamado ou Ordem de Serviço).
2. **Aprovação de Orçamento:** O gestor ou administrador analisa a solicitação comparando-a com o orçamento do Centro de Custo definido.
3. **Cotação de Preços:** O comprador lança os valores cotados com diferentes fornecedores. O sistema gera automaticamente um comparativo de preços detalhado.
4. **Pedido de Compra (PO):** Após a seleção do vencedor, é gerado um Pedido de Compra estruturado (formato PDF) para envio ao fornecedor.
5. **Recebimento de Itens:** Ao receber a mercadoria, o Almoxarifado realiza o recebimento no sistema (parcial ou total). Itens de consumo entram no estoque de manutenção, enquanto equipamentos geram automaticamente um Ativo patrimonial no inventário de TI.
6. **Contratos:** O menu **Contratos** permite gerenciar a vigência de contratos com fornecedores, exibindo alertas visuais de vencimento a partir de 90 dias.

---

## 🎛️ 11. Configurações de Módulos e Acessos por Menu (RBAC)

Os administradores têm controle total sobre as seções de menu da aplicação através do painel de Módulos:

1. Acesse o menu **Módulos** (canto superior direito no dropdown do Administrador ou em `/admin/modulos`).
2. **Ativar/Desativar Módulos Globais:** Você pode ligar ou desligar funcionalidades inteiras (como Compras e Manutenção Preventiva). Isso oculta links e bloqueia acessos a endpoints dessas seções imediatamente em todo o sistema.
3. **Matriz de Permissões de Menu:** Abaixo dos módulos, use a tabela para conceder ou revogar o acesso de visualização de cada menu principal (Ex: *Ativos*, *Compras*, *Backup*, *Usuários*) para cada Perfil de Acesso do sistema.
4. Clique em **Salvar Configurações** para aplicar instantaneamente na interface de todos os usuários.
5. *Nota de segurança:* O perfil do Administrador é travado com acesso completo a tudo por padrão para prevenir bloqueios permanentes acidentais.
