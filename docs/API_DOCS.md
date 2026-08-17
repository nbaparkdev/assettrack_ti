# AssetTrack TI - API Reference

Documentação completa dos endpoints do AssetTrack TI. A aplicação possui dois tipos de rotas:

- **API REST** (`/api/v1`): endpoints em Go (Gin) que retornam JSON para integração e consumo do frontend.
- **Rotas Web (Frontend)**: páginas Single Page Application (SPA) renderizadas via React (Vite + React Router).

---

# API REST — JSON (`/api/v1`)

## 🔐 Autenticação (`/auth`)

### POST `/auth/login`
Obtém o token JWT para acesso.

**Parâmetros (Form URL Encoded):**
| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| username | string | Sim | E-mail do usuário |
| password | string | Sim | Senha do usuário |

**Response (200 OK):**
```json
{
  "access_token": "ey...",
  "token_type": "bearer"
}
```

### POST `/auth/register`
Registra um novo usuário.

### GET `/auth/me`
Retorna os dados do usuário autenticado.

## 📦 Ativos (`/assets`)

Todos os endpoints requerem cabeçalho `Authorization: Bearer <token>`.

### GET `/assets/referencias`
Busca todas as tabelas de referência para o preenchimento de formulários e filtros de ativos.

**Response (200 OK):**
```json
{
  "categorias": [{"id": 1, "nome": "Notebooks", "descricao": "Computadores portáteis"}],
  "setores": [{"id": 1, "nome": "TI"}],
  "localizacoes": [{"id": 1, "nome": "Sede Central"}],
  "armazenamentos": [{"id": 1, "nome": "Escaninho A", "codigo": "ESC-A"}],
  "fornecedores": [{"id": 1, "nome": "Dell Brasil"}]
}
```

### GET `/assets`
Lista os ativos cadastrados.

**Query Parameters:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| skip | int | Quantidade de registros a pular (default: 0) |
| limit | int | Limite de registros a retornar (default: 100) |
| e_patrimonio | string | Busca por número de patrimônio (opcional) |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "nome": "Notebook Latitude",
    "e_patrimonio": "EP-0001",
    "status": "Disponível",
    "bloqueado": true,
    "categoria": {
      "id": 1,
      "nome": "Notebooks"
    }
  }
]
```

### POST `/assets`
Cadastra um novo ativo. (Requer permissão Admin/Gerente/Gerente Infra/Técnico)

**Body (JSON):**
```json
{
  "nome": "Monitor Dell 27",
  "e_patrimonio": "EP-0982",
  "modelo": "U2723QE",
  "descricao": "Monitor 4K IPS Black",
  "valor": 2499.90,
  "status": "Disponível",
  "numero_serie": "CN-082J29",
  "bloqueado": false,
  "requer_termo_rh": false,
  "categoria_id": 2,
  "fornecedor_id": 1,
  "current_local_id": 1,
  "current_armazenamento_id": 1
}
```

### GET `/assets/{id}`
Busca os detalhes completos de um ativo específico.

### PUT `/assets/{id}`
Atualiza dados do ativo. (Requer permissão Admin/Gerente/Gerente Infra/Técnico)

> [!NOTE]
> **Regra de Negócio de Ativos Bloqueados (Ativo Fixo):**
> Se o ativo possui a flag `"bloqueado": true` e seu status é alterado para `"Manutenção"`, o sistema realiza um snapshot do estado de localização atual (colunas `prev_*`). Durante a manutenção, qualquer alteração nas colunas de localização/setor/posse será ignorada/bloqueada para preservar a integridade. Ao final da manutenção (mudança de status para qualquer outro valor), os valores de localização anteriores são restaurados de forma automática.

### DELETE `/assets/{id}`
Remove permanentemente o ativo. (Requer permissão Admin)

### GET `/assets/{id}/qrcode`
Gera e retorna um stream de imagem em formato PNG contendo o QR Code do ativo.

### POST `/assets/scan-qr`
Escaneia uma imagem enviada via multipart/form-data e localiza o ativo associado.

**Request (Multipart Form):**
- `file`: Arquivo de imagem do QR Code.

**Response (200 OK):**
Retorna o objeto do ativo decodificado.

### POST `/assets/bulk`
Duplica um ativo base em lote com suporte a sucesso parcial e rollback interno de falhas. (Requer permissão Admin/Gerente/Gerente Infra/Técnico)

**Body (JSON):**
```json
{
  "template_id": 1,
  "copies": [
    {
      "e_patrimonio": "EP-0002",
      "numero_serie": "SN-002",
      "current_local_id": 1,
      "current_armazenamento_id": 1
    },
    {
      "e_patrimonio": "EP-0003",
      "numero_serie": "SN-003",
      "current_local_id": 1,
      "current_armazenamento_id": 1
    }
  ]
}
```

**Response (200 OK):**
```json
{
  "success_count": 2,
  "failed_count": 0,
  "results": [
    {
      "e_patrimonio": "EP-0002",
      "success": true,
      "asset_id": 12
    },
    {
      "e_patrimonio": "EP-0003",
      "success": true,
      "asset_id": 13
    }
  ]
}
```

---

## 📝 Solicitações (`/solicitacoes`)

### GET `/solicitacoes/`
Lista as solicitações do usuário logado.

### POST `/solicitacoes/`
Cria uma solicitação de ativo.

**Body (JSON):**
```json
{
  "asset_id": 5,
  "tipo": "EMPRESTIMO",
  "observacao": "Preciso para home office"
}
```

### PUT `/solicitacoes/{solicitacao_id}/approve`
Aprova uma solicitação.

### PUT `/solicitacoes/{solicitacao_id}/reject`
Rejeita uma solicitação.

---

## 🔄 Movimentações (`/movimentacoes`)

### GET `/movimentacoes/`
Lista o histórico de movimentações.

### POST `/movimentacoes/devolver/{asset_id}`
Registra a devolução de um ativo.

---

## 📱 QR Code (`/qr`)

### GET `/qr/me`
Retorna o token QR do usuário logado.

### POST `/qr/me/generate`
Gera um novo token QR para o usuário.

### POST `/qr/login`
Autenticação via QR Code.

**Body (JSON):**
```json
{
  "token": "token-do-qr",
  "pin": "123456"
}
```

### GET `/qr/user/{token}`
Retorna o perfil público do usuário pelo token QR.

### POST `/qr/delivery/confirm`
Confirma entrega de equipamento via scanner QR.

---

## 👥 Usuários (`/users`)

### GET `/users/`
Lista todos os usuários (Admin).

### POST `/users/`
Cria um novo usuário.

### GET `/users/{user_id}`
Retorna dados de um usuário específico.

### PUT `/users/{user_id}`
Atualiza dados de um usuário.

---

# Rotas do Frontend (React Router)

As rotas abaixo representam as páginas da interface da Single Page Application (SPA) no React.
Elas não batem no backend para renderizar HTML, mas sim consomem a API REST mapeada acima.

## 📦 Ativos (`/assets`)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/assets` | Listagem de ativos com filtros | Todos |
| GET | `/assets/search` | Busca de ativos | Todos |
| GET | `/assets/scanner` | Scanner QR de ativos | Todos |
| GET | `/assets/new` | Formulário de novo ativo | Admin/Gerente/Gerente Infra |
| POST | `/assets/new` | Criar ativo | Admin/Gerente/Gerente Infra |
| GET | `/assets/reports` | Relatórios com filtros | Admin/Gerente/Gerente Infra |
| GET | `/assets/reports/pdf` | Exportar relatório em PDF | Admin/Gerente/Gerente Infra |
| GET | `/assets/admin/categorias` | Gestão de categorias | Admin/Gerente/Gerente Infra |
| POST | `/assets/admin/categorias` | Criar categoria | Admin/Gerente/Gerente Infra |
| POST | `/assets/admin/categorias/{cat_id}/delete` | Remover categoria | Admin/Gerente/Gerente Infra |
| GET | `/assets/{asset_id}` | Detalhes do ativo | Todos |
| GET | `/assets/ep/{e_patrimonio}` | Detalhes por E-Patrimônio | Todos |
| GET | `/assets/{asset_id}/edit` | Editar ativo | Admin/Gerente/Gerente Infra |
| POST | `/assets/{asset_id}/edit` | Salvar edição | Admin/Gerente/Gerente Infra |
| POST | `/assets/{asset_id}/delete` | Excluir ativo | Admin/Gerente/Gerente Infra |
| POST | `/assets/{asset_id}/transfer` | Transferir responsável | Admin/Gerente/Gerente Infra |
| POST | `/assets/{asset_id}/baixa` | Dar baixa no ativo | Admin/Gerente/Gerente Infra |
| GET | `/assets/{asset_id}/maintenance/start` | Iniciar manutenção | Técnico/Admin/Gerente |
| POST | `/assets/{asset_id}/maintenance/start` | Confirmar início | Técnico/Admin/Gerente |
| GET | `/assets/{asset_id}/maintenance/finish` | Finalizar manutenção | Técnico/Admin/Gerente |
| POST | `/assets/{asset_id}/maintenance/finish` | Confirmar finalização | Técnico/Admin/Gerente |
| POST | `/assets/{asset_id}/return` | Devolver ativo | Admin/Gerente |

---

## 🏢 Fornecedores (`/suppliers`)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/suppliers` | Lista de fornecedores | Admin/Gerente/Gerente Infra |
| GET | `/suppliers/new` | Formulário de novo fornecedor | Admin/Gerente/Gerente Infra |
| POST | `/suppliers/new` | Criar fornecedor | Admin/Gerente/Gerente Infra |
| POST | `/suppliers/parse-xml` | Upload de NF-e XML para auto-preenchimento | Admin/Gerente/Gerente Infra |
| GET | `/suppliers/{fornecedor_id}/edit` | Editar fornecedor | Admin/Gerente/Gerente Infra |
| POST | `/suppliers/{fornecedor_id}/edit` | Salvar edição | Admin/Gerente/Gerente Infra |
| POST | `/suppliers/{fornecedor_id}/delete` | Excluir fornecedor | Admin/Gerente/Gerente Infra |
| GET | `/suppliers/{fornecedor_id}/invoices` | Notas fiscais do fornecedor | Admin/Gerente/Gerente Infra |
| GET | `/suppliers/invoices/{invoice_id}` | Detalhes da nota fiscal | Admin/Gerente/Gerente Infra |
| POST | `/suppliers/{fornecedor_id}/invoices/{invoice_id}/delete` | Remover nota fiscal | Admin/Gerente/Gerente Infra |

**Campos do formulário de fornecedor (POST `/suppliers/new`):**

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| nome | string | Sim | Nome do fornecedor |
| razao_social | string | Não | Razão social |
| cnpj | string | Não | CNPJ |
| telefone | string | Não | Telefone |
| email | string | Não | E-mail de contato |
| endereco | string | Não | Endereço |
| cidade | string | Não | Cidade |
| estado | string | Não | Estado (UF) |
| tipo_fornecedor | string | Não | Tipo de fornecedor |

---

## 🎧 Service Desk (`/servicos`)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/servicos` | Dashboard e listagem de chamados | Todos |
| GET | `/servicos/novo` | Formulário de novo chamado | Todos |
| POST | `/servicos/novo` | Criar chamado | Todos |
| GET | `/servicos/chamado/{ticket_id}` | Visualizar chamado (ex: `CH-2026-0001`) | Todos |
| POST | `/servicos/chamado/{ticket_id}/update` | Atualizar status | Técnico/Admin/Gerente |
| POST | `/servicos/chamado/{ticket_id}/interacao` | Adicionar interação | Todos |
| GET | `/servicos/admin/categorias` | Gestão de categorias de serviço | Admin/Gerente |
| POST | `/servicos/admin/categorias` | Criar categoria de serviço | Admin/Gerente |
| GET | `/servicos/admin/servicos` | Gestão de serviços | Admin/Gerente |
| POST | `/servicos/admin/servicos` | Criar serviço | Admin/Gerente |

---

## 🚨 Alertas de Emergência (`/emergencia`)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| POST | `/emergencia/alert` | Acionar chamado de emergência | Usuários autenticados |
| GET | `/emergencia/stream` | Stream SSE em tempo real de novos alertas | Técnico/Admin/Gerente |
| GET | `/emergencia/historico` | Consulta de lista de alertas e contadores agregados | Técnico/Admin/Gerente |
| POST | `/emergencia/{alert_id}/atender` | Marcar alerta emergencial como atendido | Técnico/Admin/Gerente |

---

## 🛠️ Manutenção

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/solicitar-manutencao` | Formulário de solicitação | Todos |
| POST | `/solicitar-manutencao` | Criar solicitação | Todos |
| GET | `/minhas-solicitacoes-manutencao` | Minhas manutenções | Todos |
| GET | `/solicitacoes-manutencao` | Todas as manutenções | Técnico/Admin/Gerente |
| GET | `/solicitacoes-manutencao/{id}` | Detalhes da manutenção | Todos |
| POST | `/solicitacoes-manutencao/{id}/aceitar` | Aceitar manutenção | Técnico |
| POST | `/solicitacoes-manutencao/{id}/rejeitar` | Rejeitar manutenção | Técnico/Admin |
| POST | `/solicitacoes-manutencao/{id}/concluir` | Concluir manutenção | Técnico |
| POST | `/solicitacoes-manutencao/{id}/confirmar-recebimento` | Confirmar recebimento | Usuário |
| GET | `/manutencao/entrega/scanner` | Scanner de entrega | Técnico |

---

## 🏢 Setores (`/setores`)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/setores` | Lista de setores | Admin/Gerente |
| POST | `/setores/new` | Criar setor | Admin/Gerente |
| POST | `/setores/{setor_id}/delete` | Excluir setor | Admin/Gerente |

---

## 👤 Perfil e QR Code

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/profile` | Perfil do usuário | Todos |
| POST | `/profile/update` | Atualizar perfil | Todos |
| POST | `/profile/password` | Alterar senha | Todos |
| POST | `/profile/qr/generate` | Regenerar token QR | Todos |
| POST | `/profile/pin` | Configurar PIN | Todos |
| GET | `/meu-qrcode` | Visualizar QR Code pessoal | Todos |
| GET | `/qr/scanner/usuario` | Scanner de usuário | Técnico/Admin |

---

## 🤖 Assistente de Inteligência Artificial (`/api/v1/chat`)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| POST | `/api/v1/chat` | Endpoint do assistente virtual Kimi para consultas contextuais do ERP | Autenticado |

---

## ⚙️ Manutenção Preventiva (CMMS)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/manutencao/preventiva` | Dashboard CMMS | Admin/Técnico |
| GET/POST | `/manutencao/preventiva/planos` | Gestão de Planos de Manutenção | Admin/Gerente |
| GET/POST | `/manutencao/preventiva/ordens` | Gestão de Ordens de Serviço (OS) | Admin/Técnico |
| GET | `/manutencao/preventiva/calendario` | Calendário de manutenções | Admin/Técnico |
| POST | `/manutencao/preventiva/ordens/{id}/executar-checklist` | Execução de checklist de OS | Técnico |
| GET | `/manutencao/preventiva/relatorios` | Relatórios de manutenção (Preventiva vs Corretiva) | Admin/Gerente |

---

## 🛒 Compras e Suprimentos (Procurement)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/compras` | Dashboard de Compras | Comprador/Admin |
| GET/POST | `/compras/solicitacoes` | Solicitações de Compra (SC) | Todos / Comprador |
| GET/POST | `/compras/cotacoes` | Gestão de Cotações e seleção de Fornecedor Vencedor | Comprador/Admin |
| GET/POST | `/compras/pedidos` | Ordens de Compra (PO) e Recebimento de material | Comprador/Admin |
| GET | `/compras/estoque` | Controle de estoque de itens/materiais | Comprador/Admin |
| GET/POST | `/compras/produtos` | Catálogo de produtos e insumos | Comprador/Admin |

---

## 📋 Kanban (Projetos Internos)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/kanban` | Dashboard principal de Projetos | Admin/Técnico/RH/Comprador |
| GET/POST | `/kanban/projetos/novo` | Criação de Projetos/Quadros | Admin/Gerentes |
| POST | `/kanban/projetos/{id}/colunas/nova` | Gestão de Colunas do Quadro | Admin/Gerentes |
| POST | `/kanban/cards/novo` | Criação de Cards/Tarefas | Equipe |
| POST | `/kanban/cards/{id}/mover` | Movimentação Drag & Drop de Cards | Equipe |
| POST | `/kanban/cards/{id}/anexo` | Upload de anexos e vínculos de ativos | Equipe |

---

## 🤝 Recursos Humanos (RH)

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/rh/termos` | Listagem de Termos de Responsabilidade | RH/Admin |
| GET/POST | `/rh/termos/criar/{solicitacao_id}` | Emissão de novo termo a partir de solicitação | RH/Admin |
| POST | `/rh/termos/{id}/assinar` | Registro de assinatura/aceite | RH/Admin |
| GET | `/rh/termos/{id}/pdf` | Geração do Termo em PDF | RH/Admin |

---

## 🎛️ Administração e Webhooks

| Método | Rota | Descrição | Acesso |
|--------|------|-----------|--------|
| GET | `/admin/modulos` | Habilitar/Desabilitar Módulos Globais e Permissões (RBAC) | Admin |
| GET/POST | `/admin/webhooks` | Gestão de integrações Webhook (N8N, Zapier, etc) | Admin |
| GET/POST | `/admin/backup` | Gerar e restaurar backups do Banco de Dados | Admin |

---

## 🛠️ Status Codes Comuns

- **200 OK**: Sucesso.
- **201 Created**: Recurso criado.
- **400 Bad Request**: Erro de validação ou regra de negócio.
- **401 Unauthorized**: Falha na autenticação.
- **403 Forbidden**: Sem permissão.
- **404 Not Found**: Recurso não encontrado.
