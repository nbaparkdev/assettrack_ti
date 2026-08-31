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
- Porta livre: `8000` para Web. A porta `8080` fica disponivel para testes diretos da API, mas o uso normal acontece pelo endereco web.

Se o ZimaOS mostrar `Docker Compose nao encontrado`, instale o binario local do Compose com:

```bash
chmod +x scripts/zimaos_install_compose.sh
./scripts/zimaos_install_compose.sh
```

O instalador salva o binario em `.zimaos/bin/docker-compose` e os scripts `zimaos_*` usam esse caminho automaticamente. Isso evita depender de `/DATA/.docker/config.json`.

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

Exemplo:

```env
POSTGRES_PASSWORD=minha_senha_segura
DATABASE_URL=postgres://assettrack:minha_senha_segura@db:5432/assettrack?sslmode=disable
VITE_API_URL=/api/v1
```

Suba a aplicacao:

```bash
./scripts/zimaos_start.sh
```

Acesse:

```text
http://IP_DO_ZIMAOS:8000
```

## Endereco unico da aplicacao

No ZimaOS e em qualquer instalacao Docker, use somente o endereco da aplicacao:

```text
http://IP_DO_ZIMAOS:8000
```

O frontend encaminha automaticamente as chamadas para `/api/v1` pelo container web, que conversa com a API internamente no Docker. Por isso, a tela de login nao precisa receber `http://IP_DO_ZIMAOS:8080/api/v1`.

No APK Android, configure o servidor com o mesmo endereco base:

```text
http://IP_DO_ZIMAOS:8000
```

O APK adiciona `/api/v1` automaticamente.

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
