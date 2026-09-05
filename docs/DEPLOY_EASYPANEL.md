# Deploy no EasyPanel

Este perfil publica apenas o servico `web`. O Nginx dele encaminha `/api/v1`,
`/uploads` e `/health` ao servico `api` pela rede interna; banco e Redis nao
ficam expostos na internet. Ele e independente de `docker-compose.yml`, que
continua sendo o perfil de desenvolvimento local.

## Criacao do projeto

1. No EasyPanel, crie um projeto e adicione um servico do tipo **Compose** a
   partir deste repositorio Git.
2. Em **Compose file**, informe `docker-compose.easypanel.yml`.
3. Cadastre as variaveis de `.env.easypanel.example` na tela de variaveis do
   servico. Use valores aleatorios e fortes para `POSTGRES_PASSWORD` e
   `SECRET_KEY`; nao use os valores de exemplo.
4. Adicione um dominio ao servico `web`, com porta interna `80`. Ative HTTPS.
   Nao publique portas dos servicos `api`, `db` ou `redis`.
5. Faça o deploy. A primeira inicializacao aplica as migracoes automaticamente.

O campo `VITE_API_URL` deve permanecer como `/api/v1`. Isso evita CORS e faz o
portal, links de upload e o APK usarem o mesmo dominio HTTPS do EasyPanel.

## Dados persistentes

O arquivo Compose cria quatro volumes nomeados, que devem ser preservados ao
atualizar o codigo:

- `assettrack_postgres_data`: dados do PostgreSQL;
- `assettrack_redis_data`: Redis com AOF habilitado;
- `assettrack_uploads`: anexos, avatares e APK publicado;
- `assettrack_backups`: backups e arquivos temporarios de restauracao.

Um redeploy/rebuild normal preserva esses volumes. Nao use a opcao de remover
volumes ao recriar o servico. Antes de uma mudanca destrutiva, exporte um backup
do PostgreSQL e salve uma copia externa dos uploads.

## Validacao apos o deploy

Com o dominio configurado, confirme no navegador ou terminal:

```bash
curl -fsS https://SEU_DOMINIO/health
```

O retorno esperado e `{"status":"ok"}`. Depois, teste login, upload de um
anexo e download do APK, pois esses fluxos confirmam banco, Redis e o volume de
uploads.

## Atualizacoes

Envie as alteracoes ao repositorio conectado e use **Deploy** no EasyPanel. O
EasyPanel reconstruira apenas este perfil; os comandos locais como
`docker compose up`, `start_local.sh` e os scripts ZimaOS continuam usando seus
arquivos existentes e nao sao alterados por esta configuracao.
