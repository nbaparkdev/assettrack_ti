# Comandos Docker — AssetTrack TI

## Ambiente

| Serviço | Container | Porta |
|---|---|---|
| Web (FastAPI) | `assettrack_ti-web-1` | `8000` |
| Banco (PostgreSQL 15) | `assettrack_ti-db-1` | `5455` |

Docker via snap. Uvicorn sem `--reload`: mudanças em rota Python exigem restart do container; templates e estáticos são montados via volume e atualizam automaticamente.

---

## Scripts de Automação

```bash
./init_docker.sh      # Primeira inicialização (build + admin)
./update_docker.sh    # Git pull + rebuild + restart
./stop_docker.sh      # Parar containers
./reset_docker.sh     # Derrubar containers (--full: remove volumes/imagens)
./scripts/backup.sh   # Backup do banco (pg_dump)
./scripts/reset_db.sh  # Reset completo do banco (destroi volume, recria, seed admin)
```

---

## Comandos Manuais

### Status

```bash
docker ps --filter "name=assettrack_ti"
docker compose ps
docker logs assettrack_ti-web-1 --tail 50
docker logs assettrack_ti-db-1 --tail 50
```

### Subir / Parar

```bash
docker compose up -d          # Subir em background
docker compose up -d --build  # Rebuild e subir
docker compose down           # Parar e remover containers
docker compose restart web    # Reiniciar só o web
```

### Reiniciar uvicorn sem rebuild (via volume)

```bash
# Quando só código Python mudou (não Dockerfile/dependências)
docker exec assettrack_ti-web-1 python3 -c "
import os, signal
for pid in [int(p) for p in os.listdir('/proc') if p.isdigit()]:
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            cmd = f.read().decode()
        if 'python' in cmd and 'uvicorn' in cmd and 'app.main' in cmd:
            os.kill(pid, signal.SIGTERM)
            print(f'uvicorn PID {pid} reiniciado')
            break
    except:
        pass
"
```

### Container preso (AppArmor/snap bloqueando stop/kill)

```bash
# Renomear para liberar o nome
docker rename assettrack_ti-web-1 assettrack_ti-web-1-old

# Matar processo interno
docker exec assettrack_ti-web-1-old python3 -c "
import os, signal
for pid in [int(p) for p in os.listdir('/proc') if p.isdigit()]:
    try:
        with open(f'/proc/{pid}/cmdline', 'rb') as f:
            cmd = f.read().decode()
        if 'python' in cmd and 'uvicorn' in cmd and 'app.main' in cmd:
            os.kill(pid, signal.SIGTERM)
            break
    except:
        pass
"

# Aguardar sair e remover
docker rm -f assettrack_ti-web-1-old

# Subir de novo
docker compose up -d
```

### Banco de Dados

```bash
# Conectar via psql
docker exec -it assettrack_ti-db-1 psql -U user -d assettrack

# Backup manual
docker exec -t assettrack_ti-db-1 pg_dump -U user assettrack | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore
gunzip -c backup.sql.gz | docker exec -i assettrack_ti-db-1 psql -U user assettrack

# Reset DB (destroi volume, recria, seed admin)
./scripts/reset_db.sh              # Reset limpo
./scripts/reset_db.sh --backup     # Faz backup antes de resetar

# Reset DB manual (sem script)
docker compose down -v
docker compose up -d
```

### Logs

```bash
docker compose logs -f           # Todos os serviços
docker compose logs -f web       # Só web
docker compose logs --tail=100   # Últimas 100 linhas
```

### Limpeza

```bash
docker image prune -f            # Remove imagens não usadas
docker builder prune -f          # Limpa cache de build
docker system prune -f           # Remove tudo não usado (cuidado)
```
