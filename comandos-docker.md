# Comandos Docker — AssetTrack TI (Go + React)

## Ambiente

| Serviço | Container | Porta |
|---|---|---|
| Web (React/Nginx) | `assettrack_ti-web-1` | `8000` |
| API (Go/Gin) | `assettrack_ti-api-1` | `8080` |
| Banco (PostgreSQL 15) | `assettrack_ti-db-1` | `5456` |
| Cache/Rate Limit (Redis 7) | `assettrack_ti-redis-1` | `6380` |

---

## Scripts de Automação (Raiz do Projeto)

Criamos uma suíte de scripts na raiz para facilitar o uso diário:

```bash
./init_docker.sh      # Inicialização principal (Build + Start API, Web, DB, Redis)
./update_docker.sh    # Git pull + Rebuild silencioso + Restart sem downtime
./stop_docker.sh      # Parar containers com segurança (mantém banco)
./reset_docker.sh     # Derrubar containers (--full: remove volumes/banco e imagens)
./start_local.sh      # Modo Desenvolvimento Nativo (Sobe DB+Redis no docker, roda Go e React no terminal)
```

---

## Comandos Manuais Frequentes

### Status e Monitoramento

```bash
docker ps --filter "name=assettrack_ti"
docker compose ps
```

### Subir / Parar / Reiniciar

```bash
docker compose up -d          # Subir em background
docker compose up -d --build  # Rebuild e subir
docker compose down           # Parar e remover containers
docker compose restart api    # Reiniciar só a API (Go)
docker compose restart web    # Reiniciar só o Frontend (React/Nginx)
```

### Visualizar Logs

```bash
docker compose logs -f           # Ver logs de todos os 4 serviços ao vivo
docker compose logs -f api       # Logs só da API (Go)
docker compose logs -f web       # Logs só do Frontend (React)
docker compose logs --tail=100   # Últimas 100 linhas
```

---

## Manutenção do Banco de Dados

### Conectar ao Banco de Dados (psql)
```bash
docker exec -it assettrack_ti-db-1 psql -U user -d assettrack
```

### Backup Manual via Terminal
> **Nota:** Agora você pode fazer backups graficamente pela interface web acessando o menu "Admin > Backup de Dados". Caso precise fazer via terminal:
```bash
docker exec -t assettrack_ti-db-1 pg_dump -U user assettrack | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restaurar Backup
```bash
gunzip -c backup.sql.gz | docker exec -i assettrack_ti-db-1 psql -U user assettrack
```

### Reset Completo do Banco de Dados
> ⚠️ **Atenção:** Destrói todo o banco e recria um novo em branco com o Admin padrão.
```bash
./reset_docker.sh --full
./init_docker.sh
```

---

## Limpeza de Disco

Se o Docker começar a ocupar muito espaço no servidor, utilize:

```bash
docker image prune -f            # Remove imagens antigas ou não utilizadas pelo compose
docker builder prune -f          # Limpa cache temporário de build
docker system prune -f           # Remove tudo não usado (Atenção: limpará outros projetos parados)
```
