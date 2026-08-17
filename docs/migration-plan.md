# AssetTrack TI — Plano de Migração Completo

> **Python/FastAPI + Jinja2 → Go/Gin + React/TypeScript**

---

## 1. Decisões Consolidadas

| Item | Decisão |
|------|---------|
| **Repositório** | Monorepo: `backend/` + `frontend/` na raiz |
| **Dados** | Preservar — GORM AutoMigrate sobre banco existente |
| **Auth** | Big bang — nova SECRET_KEY, re-autenticação |
| **Docker** | 4 containers: `db` + `api` + `web` + `redis` |
| **Capacitor** | Fase 5 (pós-migração) |
| **Fase 1** | Auth completo (login/register/me + QR Code + PIN) + CRUD Users |

### Status Atual Observado (2026-08-17)

- **Backend Go/React TS**: Concluída a migração estrutural 100% de todos os módulos core.
- **Fase 1 (Auth/Users/QR)**: Concluída.
- **Fase 2 (Ativos/Categorias/Fornecedores)**: Concluída.
- **Fase 3 (Service Desk/Manutenção/Empréstimos)**: Concluída.
- **Fase 4 (Kanban/Alertas/Compras/RH/Preventivas/Admin)**: Concluída. O sistema de Webhooks (Dispatcher assíncrono), Backup/Restore (pg_dump) e Perfil de Usuário com Avatar estão totalmente operacionais.
- **Próxima frente prática (Fase 4 - Business Intelligence / Relatórios)**: Iniciar a construção de Relatórios e Dashboards analíticos. Estruturar visualização de métricas e exportações avançadas.

---

## 2. Arquitetura Final (Monorepo)

```
assettrack_ti/
├── backend/                     # Go API (Gin + GORM)
│   ├── cmd/server/main.go       # Entrypoint
│   ├── internal/
│   │   ├── config/config.go
│   │   ├── database/            # postgres.go, redis.go
│   │   ├── middleware/          # auth.go, cors.go, ratelimit.go, security.go
│   │   ├── models/             # user.go, asset.go, location.go, ...
│   │   ├── dto/                # auth_dto.go, user_dto.go, qr_dto.go, ...
│   │   ├── repository/        # base.go, user_repo.go, ...
│   │   ├── service/           # auth_service.go, qr_service.go, ...
│   │   ├── handler/           # auth_handler.go, user_handler.go, qr_handler.go, ...
│   │   └── router/router.go
│   ├── pkg/utils/              # datetime.go, response.go
│   ├── pkg/errors/errors.go
│   ├── Dockerfile
│   ├── go.mod / go.sum
│
├── frontend/                    # React SPA (Vite + TS)
│   ├── src/
│   │   ├── api/                # client.ts, auth.ts, users.ts
│   │   ├── components/         # ui/ (shadcn), layout/, auth/, users/
│   │   ├── hooks/              # useAuth.ts, useUsers.ts
│   │   ├── pages/              # LoginPage.tsx, DashboardPage.tsx, UsersPage.tsx
│   │   ├── stores/authStore.ts # Zustand
│   │   ├── types/              # auth.ts, user.ts
│   │   ├── App.tsx, main.tsx, index.css
│   ├── Dockerfile, nginx.conf
│   ├── package.json, vite.config.ts, tailwind.config.ts
│
├── docker-compose.yml           # Dev: db + redis + api + web
├── docker-compose.prod.yml
├── .env / .env.example
├── init_docker.sh / stop_docker.sh / update_docker.sh / reset_docker.sh
└── docs/
```

---

## 3. Docker Compose — 4 Containers

```yaml
services:
  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-assettrack}
    ports: ["5456:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d assettrack"]
      interval: 10s; timeout: 5s; retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports: ["6379:6379"]
    volumes: [redis_data:/data]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s; timeout: 5s; retries: 5

  api:
    build: { context: ./backend }
    restart: unless-stopped
    ports: ["8080:8080"]
    environment:
      DATABASE_URL: postgres://user:password@db:5432/assettrack?sslmode=disable
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      GIN_MODE: debug
    depends_on: { db: { condition: service_healthy }, redis: { condition: service_healthy } }
    volumes: [uploads_data:/app/uploads]

  web:
    build: { context: ./frontend }
    restart: unless-stopped
    ports: ["3000:80"]
    depends_on: [api]

volumes:
  postgres_data:
  redis_data:
  uploads_data:
```

---

## 4. Mapeamento de Rotas — Fase 1

| Python Endpoint | Go Endpoint | Mudanças |
|-----------------|-------------|----------|
| `POST /api/v1/auth/login` (form) | `POST /api/v1/auth/login` (JSON) | Body muda para JSON |
| `POST /api/v1/auth/register` | `POST /api/v1/auth/register` | Idêntico |
| `GET /api/v1/auth/me` | `GET /api/v1/auth/me` | Idêntico |
| `GET /api/v1/users/` | `GET /api/v1/users` | skip/limit params |
| `POST /api/v1/users/` | `POST /api/v1/users` | Idêntico |
| `GET /api/v1/users/{id}` | `GET /api/v1/users/:id` | Gin param style |
| `PUT /api/v1/users/{id}` | `PUT /api/v1/users/:id` | Gin param style |
| `GET /api/v1/qr/me` | `GET /api/v1/qr/me` | Idêntico |
| `POST /api/v1/qr/me/generate` | `POST /api/v1/qr/me/generate` | Idêntico |
| `GET /api/v1/qr/me/badge` | `GET /api/v1/qr/me/badge` | Idêntico |
| `POST /api/v1/qr/me/pin` | `POST /api/v1/qr/me/pin` | Idêntico |
| `POST /api/v1/qr/login` | `POST /api/v1/qr/login` | Idêntico |
| `GET /api/v1/qr/user/{token}` | `GET /api/v1/qr/user/:token` | Gin param style |
| `POST /api/v1/qr/delivery/confirm` | `POST /api/v1/qr/delivery/confirm` | Idêntico |

---

## 5. Mapeamento de Modelos — Fase 1

### User: SQLAlchemy → GORM

| Python | Go Struct |
|--------|-----------|
| `id: Mapped[int]` PK | `ID uint` `gorm:"primaryKey"` |
| `email: Mapped[str]` unique | `Email string` `gorm:"uniqueIndex;not null"` |
| `hashed_password: Mapped[str]` | `HashedPassword string` `gorm:"column:hashed_password;not null"` |
| `nome: Mapped[str]` | `Nome string` `gorm:"not null"` |
| `matricula: Mapped[str]` unique null | `Matricula *string` `gorm:"uniqueIndex"` |
| `cargo: Mapped[str]` null | `Cargo *string` |
| `role: Mapped[UserRole]` enum | `Role string` `gorm:"type:varchar(20);default:'usuario_comum'"` |
| `is_active: Mapped[bool]` | `IsActive bool` `gorm:"default:false"` |
| `qr_token: Mapped[str]` unique null | `QRToken *string` `gorm:"column:qr_token;uniqueIndex"` |
| `qr_token_created_at` null | `QRTokenCreatedAt *time.Time` `gorm:"column:qr_token_created_at"` |
| `pin_hash: Mapped[str]` null | `PINHash *string` `gorm:"column:pin_hash"` |
| `departamento_id: FK` | `DepartamentoID *uint` `gorm:"column:departamento_id"` |
| `avatar_url: Mapped[str]` null | `AvatarURL *string` `gorm:"column:avatar_url"` |

### UserRole Constants

```go
const (
    RoleAdmin        = "admin"
    RoleGerente      = "gerente_ti"
    RoleTecnico      = "tecnico"
    RoleGerenteInfra = "gerente_infra"
    RoleComprador    = "comprador"
    RoleUsuario      = "usuario_comum"
    RoleRH           = "rh"
)
```

### QRLog: SQLAlchemy → GORM

| Python | Go Struct |
|--------|-----------|
| `id` PK | `ID uint` `gorm:"primaryKey"` |
| `user_id` FK SET NULL | `UserID *uint` `gorm:"column:user_id"` |
| `actor_id` FK SET NULL | `ActorID *uint` `gorm:"column:actor_id"` |
| `action` enum | `Action string` `gorm:"type:varchar(30);not null"` |
| `ip_address` null | `IPAddress *string` `gorm:"column:ip_address"` |
| `details` null | `Details *string` |
| `success` bool | `Success bool` `gorm:"default:true"` |
| `timestamp` datetime | `Timestamp time.Time` `gorm:"autoCreateTime"` |

---

## 6. Compatibilidade Técnica

| Aspecto | Compatibilidade |
|---------|----------------|
| **Bcrypt hashes** | ✅ Python `$2b$` → Go `x/crypto/bcrypt` lê nativamente |
| **PostgreSQL enum** | ✅ GORM trata como varchar, coexiste com enums existentes |
| **Tabelas existentes** | ✅ GORM AutoMigrate não deleta dados/colunas |
| **JWT payload** | ✅ Mesmo formato `{sub, role, exp}`, nova SECRET_KEY |

---

## 7. Tarefas — Fase 1 (25 tasks)

| # | Tarefa | Camada |
|---|--------|--------|
| 1.1 | Go module init + project structure | Backend |
| 1.2 | Config (env vars, settings) | Backend |
| 1.3 | PostgreSQL connection (GORM) | Backend |
| 1.4 | Redis connection | Backend |
| 1.5 | User + QRLog + Departamento models | Backend |
| 1.6 | Auth + User + QR DTOs | Backend |
| 1.7 | Base repository (generic CRUD) | Backend |
| 1.8 | User repository | Backend |
| 1.9 | Auth service (JWT + bcrypt) | Backend |
| 1.10 | QR service (generation) | Backend |
| 1.11 | QR log service | Backend |
| 1.12 | Auth middleware (JWT validation) | Backend |
| 1.13 | CORS + Security headers middleware | Backend |
| 1.14 | Rate limiting middleware (Redis) | Backend |
| 1.15 | Auth handler (login/register/me) | Backend |
| 1.16 | User handler (CRUD) | Backend |
| 1.17 | QR handler (all endpoints) | Backend |
| 1.18 | Router setup + health check | Backend |
| 1.19 | Backend Dockerfile (multi-stage) | Backend |
| 1.20 | Vite + React + TS project setup | Frontend |
| 1.21 | Tailwind + Shadcn/ui setup | Frontend |
| 1.22 | API client + TypeScript types | Frontend |
| 1.23 | Auth store + Login page | Frontend |
| 1.24 | Dashboard layout + Users page | Frontend |
| 1.25 | Frontend Dockerfile + nginx.conf | Frontend |
| 1.26 | docker-compose.yml (4 containers) | DevOps |
| 1.27 | Shell scripts (init/stop/update/reset) | DevOps |

---

## 8. Acceptance Criteria — Fase 1

- [ ] `POST /api/v1/auth/login` retorna JWT válido
- [ ] `GET /api/v1/auth/me` retorna dados do usuário autenticado
- [ ] `POST /api/v1/auth/register` cria usuário (requer admin)
- [ ] `GET/POST/PUT /api/v1/users` CRUD funcional
- [ ] `POST /api/v1/qr/login` login via QR + PIN
- [ ] `POST /api/v1/qr/me/generate` gera novo QR token
- [ ] `POST /api/v1/qr/me/pin` configura PIN (4-6 dígitos)
- [ ] Rate limiting funcional via Redis
- [ ] React login page funcional
- [ ] React user management page funcional
- [ ] Docker compose sobe 4 containers healthy
- [ ] Scripts .sh funcionais (init/stop/update/reset)
- [ ] Dados existentes preservados no PostgreSQL
- [ ] Senhas bcrypt compatíveis (Python ↔ Go)

---

## 9. Fases Futuras (Resumo)

| Fase | Módulos | Models Principais |
|------|---------|-------------------|
| **2** | Assets + Suppliers | Asset, AssetCategory, Fornecedor, NotaFiscal, Location |
| **3** | Service Desk + Maintenance | ServiceTicket, Solicitacao, Movimentacao, SolicitacaoManutencao |
| **4** | Kanban + SSE + Procurement | KanbanProject/Card, EmergencyAlert, Procurement (20+ models) |
| **5** | Capacitor (Mobile) | Camera API, Push Notifications |
