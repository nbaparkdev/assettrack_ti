# AssetTrack TI - Funcionalidades

> Sistema de Gerenciamento de Ativos de TI com interface web moderna.

---

## 🔐 Autenticação & Usuários

| Funcionalidade | Rota | Descrição |
|----------------|------|-----------|
| **Login** | `/login` | Autenticação com email/senha, JWT em cookie HTTP-only |
| **Registro** | `/register` | Cadastro de novos usuários (requer aprovação admin) |
| **Logout** | `/logout` | Encerramento de sessão |
| **Perfil** | `/profile` | Visualização e edição de dados pessoais |

### Roles de Usuário
- `ADMIN` - Acesso total ao sistema
- `GERENTE_TI` - Gerencia ativos, usuários e solicitações
- `TECNICO` - Operações técnicas
- `USUARIO` - Solicitante básico

---

## 📦 Gestão de Ativos

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Listar Ativos** | `/assets` | Todos |
| **Detalhes do Ativo** | `/assets/{id}` | Todos |
| **Cadastrar Ativo** | `/assets/new` | Admin, Gerente |
| **Editar Ativo** | `/assets/{id}/edit` | Admin, Gerente |
| **Scanner QR** | `/assets/scanner` | Todos |
| **Gerar QR Code** | `/assets/{id}/qrcode` | Todos |
| **Transferir Custódia** | `/assets/{id}/transfer` | Todos (gera solicitação) |
| **Dar Baixa (Write-off)** | `/assets/{id}/baixa` | Admin, Gerente |
| **Iniciar Manutenção** | `/assets/{id}/manutencao` | Admin, Gerente |

### Campos do Ativo
- Nome, Descrição, Número de Série, Número do Patrimônio
- Categoria, Marca, Modelo
- Data de Aquisição, Valor, Fornecedor
- Status: `Disponível`, `Em Uso`, `Manutenção`, `Armazenado`, `Baixado`
- Localização: Departamento, Local, Armazenamento
- Responsável atual (Usuário)

---

## 📋 Solicitações

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Minhas Solicitações** | `/solicitacoes` | Todos |
| **Nova Solicitação** | `/solicitacoes/new` | Todos |
| **Aprovar Solicitação** | `/admin/solicitacoes/{id}/approve` | Admin, Gerente |
| **Rejeitar Solicitação** | `/admin/solicitacoes/{id}/reject` | Admin, Gerente |

### Tipos de Solicitação
- Empréstimo de equipamento
- Transferência de custódia (gera movimentação automática)

---

## 🔄 Movimentações (Log de Histórico)

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Histórico de Movimentações** | `/movimentacoes` | Admin, Gerente |

### Tipos de Movimentação
- `EMPRESTIMO` - Saída de ativo para usuário
- `DEVOLUCAO` - Retorno ao estoque
- `TRANSFERENCIA` - Mudança de responsável
- `MANUTENCAO` - Envio para reparo
- `BAIXA` - Retirada do inventário
- `CADASTRO` - Entrada inicial no sistema

---

## 🏢 Setores (Departamentos)

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Gerenciar Setores** | `/setores` | Admin, Gerente |
| **Criar Setor** | `/setores/new` | Admin, Gerente |
| **Remover Setor** | `/setores/{id}/delete` | Admin, Gerente |

---

## 👥 Administração de Usuários

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Listar Usuários** | `/admin/users` | Admin, Gerente |
| **Editar Usuário** | `/users/{id}/edit` | Admin |
| **Ativar/Desativar** | `/users/{id}/toggle-active` | Admin |

---

## 🛠️ Manutenção

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Listar Manutenções** | `/maintenance` | Admin, Gerente |
| **Registrar Manutenção** | `/assets/{id}/manutencao` | Admin, Gerente |
| **Finalizar Manutenção** | `/maintenance/{id}/complete` | Admin, Gerente |

---

## 📊 Dashboard

| Funcionalidade | Descrição |
|----------------|-----------|
| **Resumo Geral** | Cards com totais: Ativos, Em Uso, Disponíveis, Manutenção |
| **Comandos Rápidos** | Atalhos para ações frequentes |
| **Atividade Recente** | Últimas movimentações |
| **Solicitações Pendentes** | Lista de aprovações aguardando (Admin/Gerente) |

---

## 🎨 Design System

- **Estilo:** Industrial Technical
- **Características:**
  - Bordas retas (sem rounded)
  - Sombras sólidas offset
  - Tipografia monospace para labels
  - Cores: Preto, Branco, Cinzas, Acentos mínimos
  - Efeitos hover com translate

---

## 🔧 Tecnologias

| Camada | Tecnologia |
|--------|------------|
| **Backend** | FastAPI (Python 3.11+) |
| **Frontend** | Jinja2 Templates + Tailwind CSS |
| **Database** | PostgreSQL (Async SQLAlchemy) |
| **Auth** | JWT (HTTP-only cookies) |
| **QR Codes** | qrcode + html5-qrcode |

---

## 📁 Estrutura de Rotas

```
/                     → Dashboard
/login                → Login
/register             → Registro
/logout               → Logout
/profile              → Perfil do usuário
/assets/              → Gestão de ativos
/solicitacoes/        → Solicitações
/movimentacoes/       → Log de movimentações
/setores/             → Gerenciamento de setores
/admin/               → Funções administrativas
/maintenance/         → Gestão de manutenções
```

---

*Documento gerado em {{ data }}*
