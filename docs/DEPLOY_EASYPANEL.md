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
3.  Nomeie o serviço (ex: `assettrack-app`).
4.  Vá na aba **Build**:
    *   **Dockerfile Path**: Altere de `/Dockerfile` para `/Dockerfile.prod`.
    *   Clique em **Save**.

## 4. Variáveis de Ambiente (.env)
Vá na aba **Environment** do serviço da aplicação e adicione as variáveis.
**Atenção Crítica à `DATABASE_URL`!**

```properties
# Configurações Gerais
PROJECT_NAME="AssetTrack TI"
SECRET_KEY="crie-uma-senha-secreta-longa-aqui"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Configuração do Banco de Dados
# Use a URL Interna que você copiou no Passo 2.
# IMPORTANTE: Mude o início de 'postgres://' para 'postgresql+asyncpg://'
DATABASE_URL=postgresql+asyncpg://postgres:suasenha@asset-db:5432/postgres
```
*Clique em "Save" e depois "Deploy".*

## 5. Porta e Domínio
1.  Vá na aba **Domains**.
2.  Certifique-se de que a **Container Port** está definida como `8000`.
3.  Adicione seu domínio (ex: `app.seudominio.com`) ou use o domínio temporário do EasyPanel.

## 6. Criar Primeiro Usuário (Admin)
Como o banco é novo, não há usuários. Você precisa criar o admin manualmente.

1.  No serviço da aplicação, clique em **Console**.
2.  Clique em **Connect**.
3.  No terminal que abrir, execute o script de criação:
    ```bash
    python create_admin.py
    ```
4.  Siga as instruções (Email, Senha, Nome).

**Problemas Comuns:**
*   **Erro de Login "Conta não aprovada":** Se criou o usuário mas ele está inativo, rode o seguinte no console:
    ```bash
    python -c "import asyncio; from app.database import SessionLocal; from app.models.user import User; from sqlalchemy import select; asyncio.run(async def(){ async with SessionLocal() as db: r=await db.execute(select(User).filter(User.email=='admin@email.com')); u=r.scalars().first(); u.is_active=True; db.add(u); await db.commit() })()"
    ```
    *(Ou apenas edite o status se tiver acesso a um gerenciador de banco).*

cat <<EOF > activate_user.py
import asyncio
from sqlalchemy import select
from app.database import SessionLocal
from app.models.user import User
async def run():
    async with SessionLocal() as db:
        # Busca pelo email admin@example.com
        result = await db.execute(select(User).filter(User.email == "admin@example.com"))
        user = result.scalars().first()
        if user:
            user.is_active = True
            db.add(user)
            await db.commit()
            print("SUCESSO: Usuario ativado!")
        else:
            print("ERRO: Usuario nao encontrado. Verifique se o email é exatamente admin@example.com")
asyncio.run(run())
EOF
python activate_user.py

Seu deploy está concluído! ✅
