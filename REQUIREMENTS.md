
# Requisitos do Sistema - AssetTrack TI

Este documento detalha os requisitos técnicos necessários para a implantação e operação do AssetTrack TI utilizando Docker.

## 💻 Requisitos de Software

### Essenciais
- **Sistema Operacional:** Linux (Recomendado: Ubuntu 22.04 LTS ou superior). Também compatível com Windows (via Docker Desktop/WSL2) e macOS.
- **Docker Engine:** Versão 20.10.0 ou superior.
- **Docker Compose:** Versão 2.0.0 ou superior (Plugin `docker compose` ou standalone `docker-compose`).
- **Git:** Para clonagem e atualização do repositório.

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
| **8000** | Web Service (API/UI) | Acesso principal ao sistema via navegador. |
| **5455** | PostgreSQL DB | Acesso externo ao banco de dados (opcional). |

> **Importante:** Certifique-se de que estas portas não estão sendo utilizadas por outros serviços no servidor hospedeiro.

---

## ⚙️ Variáveis de Ambiente (.env)

O arquivo `.env` é fundamental para o funcionamento. Abaixo os principais campos:

| Variável | Descrição | Valor Padrão |
| :--- | :--- | :--- |
| `SECRET_KEY` | Chave para criptografia de tokens JWT | *Deve ser alterada em produção* |
| `DATABASE_URL` | String de conexão com o banco | `postgresql+asyncpg://user:password@db:5432/assettrack` |
| `FIRST_SUPERUSER` | E-mail do administrador inicial | `admin@example.com` |
| `FIRST_SUPERUSER_PASSWORD` | Senha do administrador inicial | `admin` |

---

## 📸 Dependências de Sistema (Internas)

Estas dependências já estão incluídas na imagem Docker, mas são listadas para referência:
- **Python 3.11-slim:** Base da aplicação.
- **Postgres 15-alpine:** Banco de dados.
- **libzbar0:** Biblioteca para processamento de QR Codes.
- **libpq-dev & gcc:** Drivers para conexão com PostgreSQL.
