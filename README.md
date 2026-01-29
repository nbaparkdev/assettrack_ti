
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
3.  Acesse a documentação interativa (Swagger UI):
    [http://localhost:8000/docs](http://localhost:8000/docs)

### Opção 2: Localmente (Sem Docker)
Requer Python 3.11+ e um banco de dados (PostgreSQL ou SQLite).

1.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```
    *Nota: Você precisará da lib `zbar` instalada no sistema para o QR Code funcionar (`sudo apt-get install libzbar0` no Linux).*

2.  Configure o banco no `.env` (exemplo SQLite):
    ```env
    DATABASE_URL=sqlite+aiosqlite:///./assettrack.db
    # Remova as variáveis POSTGRES_* se for usar SQLite
    ```

3.  Rode o servidor:
    ```bash
    uvicorn app.main:app --reload
    ```

## Primeiro Acesso
- O sistema cria as tabelas automaticamente ao iniciar.
- Para criar o primeiro usuário ADMIN, você pode usar um script manual ou o endpoint de registro (se habilitado temporariamente) ou inserir diretamente no banco.
- *Sugestão*: Use o endpoint `/api/v1/auth/register` (atualmente restrito a admin, mas para o primeiro uso você pode remover a dependência no código ou inserir manualmente no DB).
