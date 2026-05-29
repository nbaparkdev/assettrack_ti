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

- **USUARIO:** Consulta seus ativos, abre chamados e solicita manutenções.
- **TECNICO:** Atende chamados, gerencia manutenções e valida entregas via scanner QR.
- **GERENTE_TI:** Aprova solicitações, gerencia inventário e usuários.
- **GERENTE_INFRA:** Gestão de infraestrutura, fornecedores e categorias de ativos.
- **ADMIN:** Controle total do sistema (System Owner).
