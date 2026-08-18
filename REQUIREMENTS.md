
# Requisitos do Sistema - AssetTrack TI

Este documento detalha os requisitos técnicos necessários para executar e implantar o AssetTrack TI na arquitetura atual, com backend em Go (Gin + GORM), frontend em React/Vite, PostgreSQL e Redis.

## 💻 Requisitos de Software

### Essenciais
- **Sistema Operacional:** Linux (Recomendado: Ubuntu 22.04 LTS ou superior). Também compatível com Windows (PowerShell / Docker Desktop / WSL2) e macOS.
- **Docker Engine:** Versão 20.10.0 ou superior.
- **Docker Compose:** Versão 2.0.0 ou superior (plugin `docker compose`).
- **Git:** Para clonagem e atualização do repositório.

### Para desenvolvimento local nativo
- **Go:** 1.21 ou superior.
- **Node.js:** 20 ou superior.
- **npm:** 10 ou superior.

### Navegadores Suportados (Para o Scanner de QR Code)
- Google Chrome (Versão estável)
- Microsoft Edge
- Safari (iOS)
*Nota: É necessário acesso à câmera e suporte a conexões seguras ou configuração de flags para rede local.*

---

## ⚡ Requisitos de Hardware

### Configuração Mínima
- **Processador (CPU):** 1 Core (Dual-core recomendado).
- **Memória RAM:** 1 GB disponível para os containers.
- **Armazenamento:** 2 GB de espaço livre em disco (para imagens Docker e banco de dados inicial).

### Configuração Recomendada
- **Processador (CPU):** 2 Cores ou mais.
- **Memória RAM:** 2 GB ou mais.
- **Armazenamento:** 10 GB+ (considerando o crescimento do banco de dados e armazenamento de fotos de ativos).

---

## 🌐 Requisitos de Rede

O sistema utiliza as seguintes portas por padrão:

| Porta | Serviço | Descrição |
| :--- | :--- | :--- |
| **3000** | Frontend React/Vite | Interface web no modo local nativo. |
| **8000** | Web Docker (Nginx) | Interface web quando a stack completa roda em Docker. |
| **8080** | API Go/Gin | Backend REST e healthcheck. |
| **5456** | PostgreSQL DB | Acesso externo ao banco de dados local. |
| **6380** | Redis | Cache e rate limiting local. |

> **Importante:** Certifique-se de que estas portas não estão sendo utilizadas por outros serviços no servidor hospedeiro.

---

## ⚙️ Variáveis de Ambiente (.env)

O arquivo `.env` é fundamental para o funcionamento. Abaixo os principais campos:

| Variável | Descrição | Valor Padrão |
| :--- | :--- | :--- |
| `SECRET_KEY` | Chave para criptografia de tokens JWT | *Deve ser alterada em produção* |
| `DATABASE_URL` | String de conexão com o PostgreSQL | `postgres://user:password@localhost:5456/assettrack?sslmode=disable` |
| `REDIS_URL` | String de conexão com o Redis | `redis://localhost:6380/0` |
| `PORT` | Porta da API Go | `8080` |
| `GIN_MODE` | Modo de execução do Gin | `debug` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Tempo de expiração do JWT | `60` |

---

## 📸 Dependências de Sistema (Internas)

Estas dependências já estão incluídas na stack atual, mas são listadas para referência:
- **Go 1.21+**: Runtime da API.
- **Node.js 20+**: Runtime do frontend e toolchain Vite.
- **PostgreSQL 15**: Banco de dados principal.
- **Redis 7**: Cache, notificações leves e rate limiting.
- **libzbar0**: Biblioteca para leitura de QR Codes.
- **Nginx**: Entrega do frontend no modo Docker completo.
