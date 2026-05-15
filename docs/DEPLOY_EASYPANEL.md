# Guia de Deploy no EasyPanel 🚀

Este guia detalha o processo para implantar o **AssetTrack TI** utilizando a plataforma EasyPanel (Docker).

## 1. Preparação
Certifique-se de que todo o código está atualizado no seu repositório GitHub.
O projeto já conta com um `Dockerfile.prod` otimizado.

## 2. Criar Serviço de Banco de Dados (PostgreSQL)
Recomendamos criar o banco separado da aplicação.

1.  No seu projeto no EasyPanel, clique em **+ Service** -> **PostgreSQL**.
2.  Nomeie como preferir (ex: `asset-db`).
3.  Clique em **Create**.
4.  Após iniciar, clique no card do serviço e vá em **Connection Details**.
5.  Copie a **Internal Connection URL**. Ela será parecida com:
    `postgres://postgres:senha@asset-db:5432/postgres`

## 3. Criar Serviço da Aplicação
1.  Clique em **+ Service** -> **App**.
2.  Conecte seu GitHub e selecione o repositório `assettrack_ti`.
3.  Vá na aba **Build**:
    *   **Dockerfile Path**: Altere de `/Dockerfile` para `/Dockerfile.prod`.
    *   Clique em **Save**.

## 4. Variáveis de Ambiente (.env)
Vá na aba **Environment** do serviço da aplicação e adicione as variáveis.

```properties
# Configurações Gerais
PROJECT_NAME="AssetTrack TI"
SECRET_KEY="crie-uma-senha-secreta-longa-aqui"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Configuração do Banco de Dados
# IMPORTANTE: Mude o início de 'postgres://' para 'postgresql+asyncpg://'
DATABASE_URL=postgresql+asyncpg://postgres:suasenha@asset-db:5432/postgres
```

## 5. Porta e Domínio
1.  Vá na aba **Domains**.
2.  Certifique-se de que a **Container Port** está definida como `8000`.

## 6. Inicializar Usuário (Admin)
Como o banco é novo, você precisa criar e ativar o admin manualmente no console do container.

1.  No serviço da aplicação, clique em **Console**.
2.  Execute os comandos de inicialização:
    ```bash
    # Criar o usuário
    python create_admin.py
    
    # Ativar o usuário (Obrigatório para login)
    python activate_user_admin.py
    ```

Seu deploy está concluído! ✅
