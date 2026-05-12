# 📘 Manual do Usuário - AssetTrack TI

Bem-vindo ao manual oficial do **AssetTrack TI**, o sistema completo para gerenciamento e controle de ativos de TI. Este guia cobre desde o acesso básico até funcionalidades avançadas para administradores e técnicos.

---

## 📑 Índice

1. [Acesso e Autenticação](#1-acesso-e-autenticação)
2. [Painel Principal (Dashboard)](#2-painel-principal-dashboard)
3. [Gestão de Ativos](#3-gestão-de-ativos)
    - [Consultar Ativos](#consultar-ativos)
    - [Transferir e Assumir Responsabilidade](#transferir-e-assumir-responsabilidade)
4. [Manutenção](#4-manutenção)
    - [Solicitar Manutenção](#solicitar-manutenção)
    - [Acompanhar Solicitações](#acompanhar-solicitações)
    - [Fluxo do Técnico](#fluxo-do-técnico)
5. [Service Desk (Chamados)](#5-service-desk-chamados)
6. [Sistema QR Code](#6-sistema-qr-code)
    - [Configurar PIN](#configurar-pin)
    - [Meu Crachá Digital](#meu-crachá-digital)
    - [Scanner](#scanner)
7. [Perfis de Acesso](#7-perfis-de-acesso)

---

## 1. 🔐 Acesso e Autenticação

Existem duas formas de acessar o sistema:

### Login Tradicional
1. Acesse a página de login (`/login`).
2. Digite seu **Email** e **Senha**.
3. Clique em **Entrar**.

### Login via QR Code
Ideal para acesso rápido em dispositivos compartilhados ou tablets.
1. Na tela de login, clique em **"Login com QR Code"** ou acesse `/login/qr`.
2. Aponte a câmera para o seu **Crachá Digital (QR Code)**.
3. Digite seu **PIN de segurança** (4 a 6 dígitos).
4. O acesso será liberado instantaneamente.

> [!NOTE]
> Se você ainda não configurou seu PIN, acesse via email/senha primeiro e configure-o no menu "Meu QR Code".

---

## 2. 📊 Painel Principal (Dashboard)

Ao entrar, você verá o Dashboard com informações relevantes ao seu perfil.

- **Resumo Geral**: Cards mostrando total de ativos, itens em uso, em manutenção e disponíveis (Visível para Admins/Gerentes).
- **Ações Rápidas**: Botões para as tarefas mais comuns, como "Novo Ativo" ou "Solicitar Manutenção".
- **Atividade Recente**: Histórico das últimas movimentações no sistema.
- **Solicitações Pendentes**: Lista de pedidos que aguardam sua aprovação.

---

## 3. 📦 Gestão de Ativos

### Consultar Ativos
Acesse o menu **"Ativos"** para ver a listagem completa.
- Use a **Barra de Pesquisa** para buscar por nome, modelo, número de série ou patrimônio.
- Use os **Filtros** para refinar por status (Em Uso, Disponível, Manutenção) ou localização.
- Clique em **"Ver Detalhes"** para acessar o histórico completo de um ativo.

### Transferir e Assumir Responsabilidade
Para mover um ativo de um usuário para outro:
1. Vá nos detalhes do ativo.
2. Clique em **"Transferir"**.
3. Selecione o **Novo Responsável**.
4. Uma solicitação será gerada e o novo responsável deverá aceitar (ou um admin pode aprovar diretamente).

---

## 4. 🛠️ Manutenção

Se um equipamento apresentar defeito, você pode solicitar reparo diretamente pelo sistema.

### Solicitar Manutenção
1. Acesse o menu **"Solicitar Manutenção"**.
2. Selecione o **Ativo** que está com problema (apenas ativos sob sua responsabilidade aparecerão).
3. Descreva o problema detalhadamente.
4. Clique em **Enviar**.
5. O status do ativo mudará para "Manutenção" assim que um técnico aceitar o chamado.

### Acompanhar Solicitações
Em **"Minhas Solicitações"**, você pode ver o status de todos os seus pedidos:
- 🟡 **Pendente**: Aguardando um técnico aceitar.
- 🔵 **Em Andamento**: Equipamento em reparo.
- 🟠 **Aguardando Entrega**: Reparo concluído, aguardando você retirar/receber.
- 🟢 **Concluída**: Equipamento devolvido e confirmado.

### Fluxo do Técnico (Para perfis Técnico/Admin)
1. **Painel de Solicitações**: Visualize chamados pendentes em `/solicitacoes-manutencao`.
2. **Aceitar**: Clique em "Aceitar" para iniciar o trabalho.
3. **Registrar Serviço**: Durante o reparo, registre observações e peças trocadas.
4. **Concluir**: Ao finalizar, marque como "Concluído". O usuário será notificado para buscar o equipamento.
5. **Validar Entrega**:
   - Quando o usuário for retirar o equipamento, clique em **"Validar Entrega"**.
   - Use o **Scanner** para ler o QR Code do usuário e confirmar a identidade dele na hora.

---

## 5. 🎧 Service Desk (Chamados)

O módulo de **Service Desk** permite que usuários abram chamados para suporte técnico e infraestrutura.

### Abrir um Novo Chamado
1. No menu lateral ou superior, acesse **"Service Desk"**.
2. Clique em **"Novo Chamado"**.
3. Escolha o **Título**, selecione o **Serviço** desejado e a **Prioridade**.
4. Descreva o problema ou solicitação e clique em **Criar Chamado**.

### Buscar e Filtrar Chamados
Na tela principal do Service Desk (`/servicos/`), você pode usar a barra de filtros para localizar chamados rapidamente:
- **Buscar**: Digite o código do chamado (ex: CH-2024-0001), título ou parte da descrição.
- **Categoria/Setor**: Filtre por tipos específicos de serviço.
- **Status e Prioridade**: Localize chamados abertos, em atendimento ou resolvidos.
- **Data**: Defina um intervalo de datas (Início e Fim) para ver chamados abertos naquele período.

### Interagir em um Chamado
1. Clique em **"Ver Detalhes"** em qualquer chamado da lista.
2. Você verá o histórico completo de mensagens.
3. No campo de **Mensagem**, digite sua atualização ou dúvida e clique em **Enviar**.
4. Técnicos e administradores também usarão este campo para responder a você.

### QR Code do Chamado
Cada chamado possui um QR Code na página de detalhes.
- Técnicos podem escanear o QR Code impresso ou na tela do usuário para acessar o chamado e atualizar o status rapidamente.
- Usuários podem escanear para acompanhar o andamento pelo celular.

---

## 6. 📱 Sistema QR Code

O sistema possui uma forte integração com QR Codes para agilizar processos.

### Configurar PIN
Para usar o login via QR, você precisa de um PIN.
1. Acesse **"Meu QR Code"** no menu.
2. Vá na aba **"Configurar PIN"**.
3. Escolha uma senha numérica de 4 a 6 dígitos.

### Meu Crachá Digital
Em **"Meu QR Code"**, você visualiza seu código pessoal.
- Use este código para **Login Rápido**.
- Apresente este código para um técnico ao **retirar um equipamento** (validação de identidade).
- Se achar que seu QR Code vazou, clique em **"Regenerar Token"** para invalidar o anterior e criar um novo.

### Scanner (`/assets/scanner`)
O sistema possui um leitor de QR Code integrado, acessível via:
1.  **Menu Principal** (ícone de Câmera no topo ou menu mobile).
2.  **Lista de Ativos** (Botão "SCANNER").

**Funcionalidades:**
-   **Escanear Ativo**: Abre imediatamente a página de detalhes do equipamento.
    -   Exibe especificações técnicas + **Histórico Completo** (Movimentações, Manutenções e Solicitações recentes).
-   **Escanear Usuário**: (Apenas Admins) Abre o perfil público do usuário para validação ou entrega.

---

## 7. 👥 Perfis de Acesso

Entenda o que cada função pode fazer:

| Perfil | Acesso Principal |
| :--- | :--- |
| **USUARIO** | Ver seus ativos, solicitar manutenção, usar QR Code pessoal. |
| **TECNICO** | Tudo do Usuário + Atender chamados de manutenção, validar entregas. |
| **GERENTE_TI** | Tudo do Técnico + Cadastrar/Editar ativos, gerenciar estoque, aprovar solicitações. |
| **ADMIN** | Acesso total ao sistema, incluindo criação de usuários e configurações avançadas. |

---

> **Precisa de ajuda?** Entre em contato com o suporte de TI ou abra um chamado na central de ajuda.
