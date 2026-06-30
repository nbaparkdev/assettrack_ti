#!/usr/bin/env python3
"""
Debugger unificado do AssetTrack TI.

Verifica:
1. Assets - status, relacionamentos, integridade
2. Usuários - quantidade, roles, ativação
3. Transferências - lógica de solicitação (dry-run)
4. Baixas - lógica de write-off (dry-run)
5. Banco de dados - contagens, consistência

Uso:
    .venv/bin/python debugger.py
    .venv/bin/python debugger.py --fix-solicitante  # corrige bug de solicitante_id
"""

import argparse
import asyncio
import sys
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.asset import Asset, AssetStatus
from app.models.transaction import Movimentacao, Solicitacao, TipoMovimentacao, StatusSolicitacao
from app.models.location import Localizacao
from app.models.asset_category import AssetCategory
from app.crud import asset as asset_crud


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def ok(msg: str):
    print(f"  [OK]   {msg}")


def warn(msg: str):
    print(f"  [WARN] {msg}")


def err(msg: str):
    print(f"  [ERR]  {msg}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

async def check_database_counts(db):
    """Contagem geral de registros."""
    banner("Contagem de Registros")

    counts = {}
    for name, model in [
        ("Users", User),
        ("Assets", Asset),
        ("Movimentacoes", Movimentacao),
        ("Solicitacoes", Solicitacao),
        ("Localizacoes", Localizacao),
        ("Categorias", AssetCategory),
    ]:
        result = await db.execute(select(func.count()).select_from(model))
        counts[name] = result.scalar()
        print(f"  {name:20s}: {counts[name]}")

    # Alertas
    if counts["Users"] < 2:
        warn("Menos de 2 usuários cadastrados — transferências não podem ser testadas.")
    if counts["Assets"] == 0:
        err("Nenhum asset cadastrado!")
    if counts["Localizacoes"] == 0:
        warn("Nenhuma localização cadastrada.")


async def check_assets(db):
    """Verifica integridade dos assets."""
    banner("Assets")

    result = await db.execute(
        select(Asset)
        .options(
            selectinload(Asset.current_user),
            selectinload(Asset.categoria),
            selectinload(Asset.current_local),
        )
    )
    assets = result.scalars().all()

    if not assets:
        err("Nenhum asset encontrado.")
        return

    for asset in assets:
        status_type = type(asset.status).__name__
        has_value = hasattr(asset.status, 'value')
        status_repr = asset.status.value if has_value else str(asset.status)

        print(f"  ID {asset.id}: {asset.nome!r}")
        print(f"    Patrimônio : {asset.e_patrimonio}")
        print(f"    Status     : {status_repr} (type={status_type})")
        print(f"    Bloqueado  : {asset.bloqueado}")
        print(f"    CurrentUser: {asset.current_user.nome if asset.current_user else 'None'}")
        print(f"    Categoria  : {asset.categoria.nome if asset.categoria else 'None'}")
        print(f"    Local      : {asset.current_local.nome if asset.current_local else 'None'}")

        # Validações
        if asset.status == AssetStatus.BAIXADO and asset.current_user_id is not None:
            warn(f"Asset {asset.id} está BAIXADO mas ainda tem current_user_id={asset.current_user_id}")
        if asset.bloqueado and asset.status == AssetStatus.EM_USO and asset.current_user_id is None:
            warn(f"Asset {asset.id} está bloqueado e EM_USO sem usuário — possível inconsistência.")

    ok(f"{len(assets)} asset(s) verificado(s).")


async def check_users(db):
    """Verifica usuários."""
    banner("Usuários")

    result = await db.execute(select(User))
    users = result.scalars().all()

    if not users:
        err("Nenhum usuário encontrado.")
        return

    for user in users:
        active = "ATIVO" if user.is_active else "INATIVO"
        print(f"  ID {user.id}: {user.nome!r} | role={user.role.value} | {active}")

    # Verifica se há admin ativo
    admins = [u for u in users if u.role == UserRole.ADMIN and u.is_active]
    if not admins:
        warn("Nenhum administrador ativo encontrado!")
    else:
        ok(f"{len(admins)} administrador(es) ativo(s).")


async def check_transfer_logic(db):
    """Simula criação de solicitação de transferência (dry-run)."""
    banner("Lógica de Transferência (Dry-Run)")

    result = await db.execute(select(User))
    users = result.scalars().all()
    if len(users) < 2:
        warn("Precisa de pelo menos 2 usuários para testar transferência.")
        return

    result = await db.execute(select(Asset).filter(Asset.status != AssetStatus.BAIXADO).limit(1))
    asset = result.scalars().first()
    if not asset:
        warn("Nenhum asset ativo disponível para transferência.")
        return

    user_a = users[0]
    user_b = users[1]

    print(f"  Asset : {asset.id} ({asset.nome})")
    print(f"  De    : {user_a.id} ({user_a.nome})")
    print(f"  Para  : {user_b.id} ({user_b.nome})")

    try:
        # CORREÇÃO: solicitante_id deve ser quem solicita (user_a), não o destinatário
        solicitacao = Solicitacao(
            solicitante_id=user_a.id,
            asset_id=asset.id,
            motivo=f"[TRANSFERÊNCIA] Para user ID {user_b.id}: Debug test",
            status=StatusSolicitacao.PENDENTE,
            data_solicitacao=datetime.now(timezone.utc),
        )

        db.add(solicitacao)
        await db.flush()
        ok("Flush da solicitação bem-sucedido.")
        await db.rollback()
        ok("Rollback realizado. Lógica de transferência está OK.")

    except Exception as e:
        err(f"Falha na lógica de transferência: {e}")
        await db.rollback()
        raise


async def check_baixa_logic(db):
    """Simula baixa de asset (dry-run)."""
    banner("Lógica de Baixa (Dry-Run)")

    result = await db.execute(select(Asset).filter(Asset.status != AssetStatus.BAIXADO).limit(1))
    asset = result.scalars().first()
    if not asset:
        warn("Nenhum asset ativo para baixar.")
        return

    result = await db.execute(select(User).limit(1))
    current_user = result.scalars().first()

    print(f"  Asset: {asset.id} ({asset.nome}) — Status: {asset.status.value}")
    print(f"  User : {current_user.id} ({current_user.nome})")

    try:
        previous_user = asset.current_user_id

        asset.status = AssetStatus.BAIXADO
        asset.current_user_id = None

        movimentacao = Movimentacao(
            asset_id=asset.id,
            tipo=TipoMovimentacao.BAIXA,
            de_user_id=previous_user,
            para_user_id=None,
            observacao=f"Baixa efetuada por {current_user.nome}",
        )

        db.add(asset)
        db.add(movimentacao)
        await db.flush()
        ok("Flush da baixa bem-sucedido.")
        await db.rollback()
        ok("Rollback realizado. Lógica de baixa está OK.")

    except Exception as e:
        err(f"Falha na lógica de baixa: {e}")
        await db.rollback()
        raise


async def check_crud_asset_get(db):
    """Testa CRUDAsset.get com eager loading."""
    banner("CRUD Asset.get")

    result = await db.execute(select(Asset).limit(1))
    first = result.scalars().first()
    if not first:
        warn("Nenhum asset para testar CRUD.")
        return

    try:
        asset = await asset_crud.asset.get(db, id=first.id)
        print(f"  Asset ID {asset.id}: {asset.nome}")
        print(f"  Current User: {asset.current_user.nome if asset.current_user else 'None'}")
        ok("CRUDAsset.get funcionou corretamente.")
    except Exception as e:
        err(f"CRUDAsset.get falhou: {e}")
        raise


async def fix_solicitante_bug(db):
    """
    Verifica se há Solicitacoes com solicitante_id incorreto.
    O bug antigo sobrescrevia solicitante_id com destinatario_id.
    """
    banner("Verificação do Bug solicitante_id")

    result = await db.execute(select(Solicitacao))
    solicitacoes = result.scalars().all()

    if not solicitacoes:
        ok("Nenhuma solicitação no banco — nada a verificar.")
        return

    issues = []
    for s in solicitacoes:
        # Se o motivo indica transferência para X mas solicitante_id != X,
        # pode ser inconsistência (ou pode ser correto, dependendo da regra de negócio)
        if "[TRANSFERÊNCIA]" in (s.motivo or ""):
            # Extrai destinatário do motivo se possível
            import re
            match = re.search(r"Para user ID (\d+)", s.motivo)
            if match:
                dest_id = int(match.group(1))
                if s.solicitante_id == dest_id:
                    issues.append(s)
                    warn(f"Solicitação {s.id}: solicitante_id ({s.solicitante_id}) == destinatário_id ({dest_id}) — possível bug!")

    if issues:
        print(f"\n  Encontradas {len(issues)} solicitação(ões) com possível bug.")
        print("  (As solicitações antigas podem precisar de revisão manual)")
    else:
        ok("Nenhuma inconsistência de solicitante_id detectada.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Debugger do AssetTrack TI")
    parser.add_argument(
        "--fix-solicitante",
        action="store_true",
        help="Verifica inconsistências no campo solicitante_id",
    )
    args = parser.parse_args()

    print("AssetTrack TI — Debugger Unificado")
    print(f"Iniciado em: {datetime.now().isoformat()}")

    async with SessionLocal() as db:
        await check_database_counts(db)
        await check_users(db)
        await check_assets(db)
        await check_crud_asset_get(db)
        await check_transfer_logic(db)
        await check_baixa_logic(db)

        if args.fix_solicitante:
            await fix_solicitante_bug(db)

    banner("Fim")
    print("Debugger concluído com sucesso.")


if __name__ == "__main__":
    asyncio.run(main())
