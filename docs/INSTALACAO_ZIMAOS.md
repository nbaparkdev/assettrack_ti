# Instalacao no ZimaOS

Este perfil roda o AssetTrack TI em Docker Compose sem alterar o ambiente local padrao do projeto.

Arquivos usados somente no ZimaOS:

- `.env.zimaos`
- `.env.zimaos.example`
- `docker-compose.zimaos.yml`
- `scripts/zimaos_start.sh`
- `scripts/zimaos_stop.sh`
- `scripts/zimaos_status.sh`

## Requisitos

- ZimaOS com Docker ativo
- Docker Compose v2 (`docker compose`) ou o comando legado `docker-compose`
- Git, se for clonar direto no ZimaOS
- Portas livres: `8000` para Web e `8080` para API

## Instalar

```bash
cd /DATA/AppData
git clone <URL_DO_REPOSITORIO> assettrack_ti
cd assettrack_ti
chmod +x scripts/zimaos_*.sh scripts/*.sh
cp .env.zimaos.example .env.zimaos
```

Edite `.env.zimaos` e ajuste:

- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`, usando a mesma senha do Postgres
- `VITE_API_URL`, usando o IP ou dominio do ZimaOS

Exemplo:

```env
POSTGRES_PASSWORD=minha_senha_segura
DATABASE_URL=postgres://assettrack:minha_senha_segura@db:5432/assettrack?sslmode=disable
VITE_API_URL=http://192.168.1.50:8080/api/v1
```

Suba a aplicacao:

```bash
./scripts/zimaos_start.sh
```

Acesse:

```text
http://IP_DO_ZIMAOS:8000
```

## Operacao

Ver status:

```bash
./scripts/zimaos_status.sh
```

Parar:

```bash
./scripts/zimaos_stop.sh
```

Atualizar apos `git pull`:

```bash
./scripts/zimaos_start.sh
```

## APK Android

O APK nao e gerado automaticamente pela aplicacao. Gere pelo terminal e anexe:

```bash
./scripts/publish_mobile_apk.sh /caminho/AssetTrack-TI.apk
```

O arquivo fica em `backend/uploads` e aparece no download do portal.

## Dados persistentes

O perfil ZimaOS usa o project name `assettrack-zimaos`, entao os volumes Docker ficam separados do ambiente local padrao:

- `assettrack-zimaos_zimaos_postgres_data`
- `assettrack-zimaos_zimaos_redis_data`
- `assettrack-zimaos_zimaos_backups_data`

Uploads e APKs ficam em:

```text
backend/uploads
```
