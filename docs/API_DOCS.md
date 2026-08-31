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

## 📢 Avisos do Sistema (`/avisos`)

### POST `/avisos/upload`
Realiza o upload de arquivos de imagem (PNG/JPG/WEBP) ou vídeo (MP4/WEBM) de até 100MB para anexar em comunicados do sistema.

**Header:** `Authorization: Bearer <token>` (Requer perfil Admin, Gerente ou Técnico)

**Response (200 OK):**
```json
{
  "url": "/uploads/avisos/1787496015.mp4"
}
```

---

## 📱 Aplicativo Android & APK (`/app`)

### GET `/app/version`
Retorna as informações sobre a versão oficial compilada do APK Android.

**Response (200 OK):**
```json
{
  "version_code": 20260824103045,
  "version_name": "2026.08.24.1030",
  "release_date": "2026-08-24T13:30:45Z",
  "download_url": "/api/v1/app/download",
  "apk_filename": "AssetTrack-TI-v2026.08.24.1030.apk",
  "apk_size_bytes": 5885123,
  "apk_size_formatted": "5.6 MB",
  "min_android_version": "Android 7.0 (Nougat) ou superior",
  "release_notes": "• APK anexado manualmente após build realizado via terminal..."
}
```

### GET `/app/download`
Transmite o arquivo binário `.apk` mais recente via HTTP com cabeçalhos para download direto no navegador ou smartphone. O nome do arquivo é derivado do manifest gerado ao anexar o APK manualmente com `scripts/publish_mobile_apk.sh /caminho/AssetTrack-TI.apk`.

---

# Rotas do Frontend (React Router)

As rotas abaixo representam as páginas atuais da SPA em React. Elas são renderizadas no frontend e consomem a API REST em `/api/v1`.

| Rota | Página |
|------|--------|
| `/` | Dashboard principal |
| `/login` | Login |
| `/users` | Usuários |
| `/assets` | Ativos & Inventário, incluindo filtros e relatórios |
| `/badge` | Meu crachá / QR |
| `/servicos` | Service Desk |
| `/manutencoes` | Manutenções corretivas |
| `/emprestimos` | Empréstimos e devoluções |
| `/fornecedores` | Fornecedores |
| `/setores` | Setores |
| `/manutencao-preventiva` | Manutenção preventiva |
| `/kanban` | Kanban |
| `/alertas` | Alertas de emergência |
| `/compras` | Compras / Procurement |
| `/rh` | Portal RH |
| `/webhooks` | Webhooks |
| `/backups` | Backup & Restore |
| `/profile` | Perfil |
| `/configuracoes` | Configurações administrativas |
| `/logs-email` | Logs de e-mail |

## Observações importantes da arquitetura atual

- A UI não usa mais rotas HTML server-side como `/assets/new`, `/admin/modulos` ou `/servicos/novo`.
- Exportação de relatórios de ativos é feita via `GET /api/v1/assets/export.csv`.
- Configurações administrativas são feitas via `GET/PUT /api/v1/admin/settings`.
- Alertas aceitam dois estágios operacionais distintos: `ciente` e `atendido`.
- A manutenção preventiva possui rotas REST próprias em `/api/v1/preventiva/*`.

---

## 🛠️ Status Codes Comuns

- **200 OK**: Sucesso.
- **201 Created**: Recurso criado.
- **400 Bad Request**: Erro de validação ou regra de negócio.
- **401 Unauthorized**: Falha na autenticação.
- **403 Forbidden**: Sem permissão.
- **404 Not Found**: Recurso não encontrado.
