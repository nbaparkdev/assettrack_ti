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
  "e_patrimonio": "EP-1234",
  "numero_serie": "MON12345",
  "modelo": "24MK600",
  "status": "Disponível",
  "valor": 800.00,
  "data_aquisicao": "2024-01-01",
  "fornecedor_id": 2
}
```

---

## 📝 Solicitações (`/solicitacoes`)

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

---

## 📱 QR Code (`/qr`)

### GET `/qr/me`
Retorna o token QR do usuário logado.

### POST `/qr/login`
Autenticação via QR Code.

**Body (JSON):**
```json
{
  "token": "token-do-qr",
  "pin": "123456"
}
```

---

## 🛠️ Status Codes Comuns

- **200 OK**: Sucesso.
- **201 Created**: Recurso criado.
- **400 Bad Request**: Erro de validação ou regra de negócio.
- **401 Unauthorized**: Falha na autenticação.
- **403 Forbidden**: Sem permissão.
- **404 Not Found**: Recurso não encontrado.
