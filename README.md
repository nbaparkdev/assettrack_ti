
# README - AssetTrack TI

Sistema de Controle de Ativos de TI completo em Python (FastAPI).

## Estrutura
- **app/models**: Modelos do Banco de Dados (SQLAlchemy)
- **app/schemas**: Schemas de Validação (Pydantic)
- **app/api**: Endpoints da API REST
- **app/services**: Serviços de QR Code e Email

## Como Rodar

### Opção 1: Docker (Recomendado)
Certifique-se de ter Docker e Docker Compose instalados.

1.  Crie o arquivo `.env` (opcional, pois o docker-compose já define defaults principais):
    ```bash
    cp .env.example .env
    ```
2.  Suba os containers:
    ```bash
    docker-compose up --build
    ```
3.**  **Acesse a documentação interativa (Swagger UI):
    [http://localhost:8000/docs](http://localhost:8000/docs)



### Opção 2: Localmente (Sem Docker) - Modo Automático (Recomendado)
Scripts que automatizam a criação do ambiente, instalação de dependências e configuração do banco.

**Windows (PowerShell):**
1. Abra o terminal na pasta do projeto.
2. Execute o script:
   ```powershell
   .\setup.ps1
   ```

**Linux / macOS:**
1. Abra o terminal na pasta do projeto.
2. Dê permissão de execução (apenas na primeira vez):
   ```bash
   chmod +x setup.sh
   ```
3. Execute o script:
   ```bash
   ./setup.sh
   ```

### Opção 3: Localmente (Sem Docker) - Modo Manual
Requer Python 3.11+ e um banco de dados (PostgreSQL ou SQLite).

1.  **Crie e ative o ambiente virtual (venv):**
    ```bash
    # Criar venv (se ainda não existir)
    python3 -m venv venv

    # Ativar venv (Linux/macOS)
    source venv/bin/activate

    # Ativar venv (Windows PowerShell)
    .\venv\Scripts\Activate.ps1
    ```

2.  **Instale as dependências (dentro do venv):**
    ```bash
    pip install -r requirements.txt

3.   DATABASE_URL=sqlite+aiosqlite:///./assettrack.db ./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0
    ```

    > ⚠️ **Erro `externally-managed-environment`?**  
    > Em sistemas Linux modernos (Debian 12+, Ubuntu 23.04+), o pip do sistema é bloqueado (PEP 668).  
    > **Solução:** Certifique-se de ter ativado o venv antes de rodar `pip install`. Se o erro persistir, use o pip do venv explicitamente:
    > ```bash
    > ./venv/bin/pip install -r requirements.txt
    > ```

    *Nota: Você precisará da lib `zbar` instalada no sistema para o QR Code funcionar:*
    ```bash
    sudo apt-get install libzbar0  # Linux
    ```

3.  **Configure o banco no `.env`** (exemplo SQLite):
    ```env
    DATABASE_URL=sqlite+aiosqlite:///./assettrack.db
    # Remova as variáveis POSTGRES_* se for usar SQLite
    ```

4.  **Inicie o servidor:**
    ```bash
    uvicorn app.main:app --reload
    ```
    
    > **Acesso na Rede (Outros dispositivos):**
    > Para permitir que outros computadores/celulares acessem, os scripts já estão configurados com `--host 0.0.0.0`.
    > 1. Descubra seu IP (No Windows: `ipconfig`, no Linux: `hostname -I`).
    > 2. O App estará acessível em `http://SEU_IP_NA_REDE:8000`.
     > *Certifique-se de que a porta 8000 está liberada no seu Firewall.*
     >
     > 📸 **Uso da Câmera (Scanner) via HTTP:**
     > Por padrão, navegadores bloqueiam a câmera em conexões HTTP (não seguras). Para liberar o acesso em sua rede local:
     > 1. No Chrome/Edge do celular/PC que vai escanear, acesse: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
     > 2. No campo "Insecure origins treated as secure", digite o endereço do servidor: `http://SEU_IP_NA_REDE:8000`
     > 3. Mude para **Enabled** e clique em **Relaunch**.
     O servidor estará disponível em `http://localhost:8000`

### 🛠️ Solução de Problemas (Local)

**Se tiver erros estranhos com pip ou imports:**
Às vezes o `venv` quebra se a pasta for movida ou renomeada. Para consertar radicalmente:

1. Apague a pasta `venv` antiga:
   ```bash
   rm -rf venv
   ```
2. Crie e instale tudo do zero:
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r requirements.txt
   ```
3. Tente rodar novamente.

## 🔑 Usuários Padrão

O sistema possui scripts para criar usuários iniciais. Credenciais sugeridas para teste:

| Perfil | Email | Senha | Acesso |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `admin` | Total (Configurações, Usuários, Ativos) |
| **Técnico** | `tecnico@example.com` | `123` | Operacional (Manutenções e Devoluções) |

### Criar usuários via terminal
Se os usuários não existirem, rode:
```bash
# Criar Admin
python3 create_admin.py

# Criar Técnico
python3 create_technician.py
```

## 📱 Sistema de QR Code

O sistema inclui funcionalidades de QR Code para identificação e login rápido.

### Funcionalidades

| Recurso | Descrição |
| :--- | :--- |
| **Crachá Digital** | Cada usuário tem um QR Code único para identificação |
| **Login via QR** | Login rápido escaneando QR + PIN de 4-6 dígitos |
| **Confirmação de Entrega** | Valida entregas de ativos via QR do usuário |
| **Histórico de Ativos** | Scanner revela histórico completo (movimentações, manutenções, solicitações) |
| **Central de Ajuda** | Manuais integrados ao sistema (`/help`) para usuários e admins |
| **Logs de Auditoria** | Todas as ações de QR são registradas |

### Segurança

- 🔒 **Rate Limiting**: 10 tentativas de login/minuto, 3 regenerações/hora
- ⏰ **Expiração**: Tokens QR expiram após 90 dias (configurável)
- 🔐 **PIN obrigatório**: Login QR requer PIN de 4-6 dígitos
- 📝 **Auditoria**: Todas as ações de QR são logadas (logins, regenerações, confirmações)

### Acessar QR Code

1. Faça login normalmente
2. Clique em **"Meu QR Code"** no menu
3. Configure seu PIN (primeira vez)
4. Compartilhe o QR para identificação

### Endpoints da API

```
POST /api/v1/qr/login          # Login via QR + PIN
POST /api/v1/qr/me/generate    # Regenerar token QR
POST /api/v1/qr/me/pin         # Configurar PIN
GET  /api/v1/qr/me             # Obter QR Code atual
GET  /api/v1/qr/user/{token}   # Consulta perfil (Admin/Gerente)
```
