# AssetTrack TI - API Reference

Esta documentação descreve os endpoints da API RESTful do AssetTrack TI (v1).

**Base URL**: `/api/v1`

---

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

### GET `/auth/me`
Retorna os dados do usuário autenticado.

**Headers:**
`Authorization: Bearer <token>`

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "admin@example.com",
  "nome": "Administrador",
  "role": "admin",
  "is_active": true
}
```

---

## 📦 Ativos (`/assets`)

### GET `/assets/`
Lista todos os ativos cadastrados.

**Query Parameters:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| skip | int | Pular N registros (paginação) |
| limit | int | Limite de registros (default: 100) |
| serial_number | string | Filtrar por Serial Number exato |

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "nome": "Notebook Dell",
    "serial_number": "XYZ123",
    "status": "DISPONIVEL",
    "modelo": "Latitude 5420",
    "created_at": "2024-01-01T12:00:00"
  }
]
```

### POST `/assets/`
Cria um novo ativo. (Requer permissão Gerente/Admin)

**Body (JSON):**
```json
{
  "nome": "Monitor LG 24",
  "serial_number": "MON12345",
  "modelo": "24MK600",
  "status": "DISPONIVEL",
  "custo": 800.00,
  "data_aquisicao": "2024-01-01",
  "departamento_id": 2
}
```

### GET `/assets/{id}/qrcode`
Gera a imagem do QR Code para o ativo.

**Response (200 OK):**
`image/png` (Binário da imagem)

### POST `/assets/scan-qr`
Decodifica uma imagem de QR Code enviada por upload.

**Body (Multipart):**
`file`: Arquivo de imagem (png/jpg).

**Response (200 OK):**
Objeto `Asset` encontrado.

---

## 📝 Solicitações (`/solicitacoes`)

### GET `/solicitacoes/`
Lista solicitações de ativos.

**Query Parameters:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| pending_only | bool | Se `true`, retorna apenas pendentes (Gerente) |

**Comportamento:**
- **Usuário Comum**: Vê apenas suas próprias solicitações.
- **Gerente/Admin**: Vê todas (padrão) ou filtra pendentes.

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

### PUT `/solicitacoes/{id}/approve`
Aprova uma solicitação pendente. (Gerente/Admin)
*Gera automaticamente movimentação e atualiza status do ativo para `EM_USO`.*

### PUT `/solicitacoes/{id}/reject`
Rejeita uma solicitação pendente.

---

## 🔄 Movimentações (`/movimentacoes`)

### GET `/movimentacoes/`
Histórico de movimentações de ativos.

**Query Parameters:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| asset_id | int | Filtrar histórico de um ativo específico |

---

---

## 🎧 Service Desk (`/servicos`)

### GET `/servicos/` (HTML)
Lista chamados com filtros.

**Query Parameters:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| query | string | Busca por código, título ou descrição |
| status | string | Filtro por status (Aberto, Em Atendimento, Resolvido, Cancelado) |
| prioridade | string | Filtro por prioridade (Baixa, Média, Alta, Urgente) |
| categoria_id | int | ID da categoria de serviço |
| data_inicio | string | Data inicial (YYYY-MM-DD) |
| data_fim | string | Data final (YYYY-MM-DD) |

### POST `/servicos/novo` (Form)
Cria um novo chamado.

**Form Parameters:**
- `titulo`: string
- `servico_id`: int
- `prioridade`: string (Enum ServicePriority)
- `descricao`: string

### POST `/servicos/chamado/{id}/update` (Form)
Atualiza status de um chamado. (Técnico/Admin)

**Form Parameters:**
- `status`: string (Enum ServiceStatus)

### POST `/servicos/chamado/{id}/interacao` (Form)
Adiciona um comentário ao chamado.

**Form Parameters:**
- `mensagem`: string

---

## 🛠️ Status Codes Comuns

- **200 OK**: Sucesso.
- **201 Created**: Recurso criado.
- **400 Bad Request**: Erro de validação ou regra de negócio (ex: ativo já em uso).
- **401 Unauthorized**: Falha na autenticação (token ausente/inválido).
- **403 Forbidden**: Sem permissão para esta ação.
- **404 Not Found**: Recurso não encontrado.
