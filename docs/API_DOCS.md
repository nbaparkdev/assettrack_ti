# AssetTrack TI - API Reference

Documentação completa dos endpoints do AssetTrack TI. A aplicação possui dois tipos de rotas:

- **API REST** (`/api/v1`): endpoints que retornam JSON para integração com sistemas externos.
- **Rotas Web**: páginas HTML renderizadas no servidor (interface do usuário).

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

---

## 📦 Ativos (`/assets`)

### GET `/assets/`
Lista todos os ativos cadastrados.

**Query Parameters:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| skip | int | Pular N registros (paginação) |
| limit | int | Limite de registros (default: 100) |
| e_patrimonio | string | Filtrar por Número de Patrimônio exato |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "nome": "Notebook Dell",
    "e_patrimonio": "EP-0001",
    "numero_serie": "XYZ123",
    "status": "Disponível",
    "modelo": "Latitude 5420",
    "categoria_id": 1,
    "created_at": "2024-01-01T12:00:00"
  }
]
```

### POST `/assets/`
Cria um novo ativo. (Requer permissão Admin/Gerente/Gerente Infra)

**Body (JSON):**
```json
{
  "nome": "Monitor LG 24",
  "e_patrimonio": "EP-1234",
  "numero_serie": "MON12345",
  "modelo": "24MK600",
  "status": "Disponível",
  "valor": 800.00,
  "data_aquisicao": "2024-01-01",
  "fornecedor_id": 2,
  "categoria_id": 1
}
```

### GET `/assets/{asset_id}`
Retorna detalhes de um ativo específico.

### PUT `/assets/{asset_id}`
Atualiza um ativo existente.

### GET `/assets/{asset_id}/qrcode`
Retorna o QR Code do ativo.

### POST `/assets/scan-qr`
Escaneia um QR Code de ativo e retorna seus dados.

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

# Rotas Web — HTML (Interface do Usuário)

As rotas abaixo retornam páginas HTML renderizadas pelo servidor.

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

## 🛠️ Status Codes Comuns

- **200 OK**: Sucesso.
- **201 Created**: Recurso criado.
- **400 Bad Request**: Erro de validação ou regra de negócio.
- **401 Unauthorized**: Falha na autenticação.
- **403 Forbidden**: Sem permissão.
- **404 Not Found**: Recurso não encontrado.
