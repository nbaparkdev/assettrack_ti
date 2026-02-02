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
5. [Sistema QR Code](#5-sistema-qr-code)
    - [Configurar PIN](#configurar-pin)
    - [Meu Crachá Digital](#meu-crachá-digital)
    - [Scanner](#scanner)
6. [Perfis de Acesso](#6-perfis-de-acesso)

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

## 5. 📱 Sistema QR Code

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

### Scanner
O sistema possui um leitor de QR Code integrado (`/assets/scanner`).
- **Escanear Ativo**: Abre imediatamente os detalhes do equipamento.
- **Escanear Usuário**: (Apenas Admins) Abre o perfil público do usuário.

---

## 6. 👥 Perfis de Acesso

Entenda o que cada função pode fazer:

| Perfil | Acesso Principal |
| :--- | :--- |
| **USUARIO** | Ver seus ativos, solicitar manutenção, usar QR Code pessoal. |
| **TECNICO** | Tudo do Usuário + Atender chamados de manutenção, validar entregas. |
| **GERENTE_TI** | Tudo do Técnico + Cadastrar/Editar ativos, gerenciar estoque, aprovar solicitações. |
| **ADMIN** | Acesso total ao sistema, incluindo criação de usuários e configurações avançadas. |

---

> **Precisa de ajuda?** Entre em contato com o suporte de TI ou abra um chamado na central de ajuda.
