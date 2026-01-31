# AssetTrack TI - Funcionalidades

> Sistema de Gerenciamento de Ativos de TI com interface web moderna.

---

## 🔐 Autenticação & Usuários

| Funcionalidade | Rota | Descrição |
|----------------|------|-----------|
| **Login** | `/login` | Autenticação com email/senha, JWT em cookie HTTP-only |
| **Login via QR** | `/login/qr` | Autenticação alternativa com QR Code + PIN |
| **Registro** | `/register` | Cadastro de novos usuários (requer aprovação admin) |
| **Logout** | `/logout` | Encerramento de sessão |
| **Perfil** | `/profile` | Visualização e edição de dados pessoais |
| **Meu QR Code** | `/meu-qrcode` | Crachá digital com QR Code do usuário |

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

## 📱 QR Code de Usuário

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Meu QR Code** | `/meu-qrcode` | Todos (autenticados) |
| **Regenerar QR** | `/meu-qrcode/regenerar` | Todos (autenticados) |
| **Configurar PIN** | `/meu-qrcode/pin` | Todos (autenticados) |
| **Escanear QR Usuário** | `/scanner/usuario` | Admin, Gerente |
| **Perfil Público via QR** | `/usuario/{token}` | Admin, Gerente |

### Funcionalidades
- **Crachá Digital** - QR Code único para identificação
- **Login via QR + PIN** - Alternativa ao login tradicional
- **Consulta de Perfil** - Admin/Gerente podem escanear QR para ver histórico
- **Confirmação de Entrega** - Validação de entregas via QR

---

## ✅ Confirmação de Entrega

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Confirmar Entrega** | `/solicitacoes/{id}/confirmar-entrega` | Admin, Gerente |

### Fluxo de Entrega
1. Solicitação é **Aprovada** e serviço/manutenção concluído.
2. Botão "Validar Entrega" aparece para o técnico
3. Admin/Gerente deve validar a identidade do destinatário:
   - **Escanear QR do usuário** (validação forte presencial)
   - **Auto-Preencher** (⚡ validação prática rápida se identidade já confirmada)
4. Status muda para **ENTREGUE** (Aguardando usuário confirmar recebimento)
5. Usuário clica em "Confirmar Recebimento" para finalizar o processo

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

### Solicitação de Manutenção (Usuários)

| Funcionalidade | Rota | Permissão |
|----------------|------|-----------|
| **Solicitar Manutenção** | `/solicitar-manutencao` | Todos |
| **Minhas Solicitações** | `/minhas-solicitacoes-manutencao` | Todos |
| **Painel de Solicitações** | `/solicitacoes-manutencao` | Técnico, Gerente, Admin |
| **Aceitar Solicitação** | `/solicitacoes-manutencao/{id}/aceitar` | Técnico, Gerente, Admin |
| **Rejeitar Solicitação** | `/solicitacoes-manutencao/{id}/rejeitar` | Técnico, Gerente, Admin |
| **Concluir Manutenção** | `/solicitacoes-manutencao/{id}/concluir` | Técnico, Gerente, Admin |
| **Equipamentos para Retirada** | `/aguardando-entrega` | Todos |
| **Confirmar Recebimento** | `/solicitacoes-manutencao/{id}/confirmar-entrega` | Solicitante |

### Fluxo de Solicitação de Manutenção
1. **Usuário solicita** → Status `PENDENTE`
2. **Técnico aceita** → Status `EM_ANDAMENTO` + Manutenção criada
3. **Técnico conclui** → Status `AGUARDANDO_ENTREGA` + Usuário notificado
4. **Usuário confirma recebimento** → Status `CONCLUIDA` + Ativo volta para `ATIVO`

### Acompanhe o Status das Suas Solicitações
- Acesse `/minhas-solicitacoes-manutencao` para ver todas as suas solicitações
- Status: Pendente, Em Andamento, Aguardando Entrega, Concluída, Rejeitada
- Notificações automáticas quando status mudar

---

## � Segurança

| Recurso | Descrição |
|---------|-----------|
| **Rate Limiting** | Proteção contra abuso (slowapi) |
| **Expiração de Token QR** | Tokens expiram após 90 dias |
| **PIN Seguro** | Hash bcrypt, 4-6 dígitos |
| **Logs de Auditoria** | Todas ações de QR são registradas |
| **JWT HTTP-only** | Cookies seguros para autenticação |

### Limites de Taxa (Rate Limiting)
| Endpoint | Limite |
|----------|--------|
| Login QR | 10/minuto |
| Regenerar Token | 3/hora |
| Configurar PIN | 5/hora |
| Consulta Perfil | 30/minuto |

---

## �📊 Dashboard

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
/meu-qrcode           → QR Code do usuário
/login/qr             → Login via QR Code
/scanner/usuario      → Scanner QR de usuários
/usuario/{token}      → Perfil público via QR
```

---

*Documento gerado em {{ data }}*
