
# app/crud/transaction.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.crud.base import CRUDBase
from app.models.transaction import Movimentacao, Solicitacao, StatusSolicitacao
from app.schemas.transaction import (
    MovimentacaoCreate, SolicitacaoCreate, SolicitacaoUpdate
)

# Como Movimentacao não tem Update geralmente (é histórico), usamos BaseModel genérico se necessário ou criamos um schema vazio
from pydantic import BaseModel
class MovimentacaoUpdate(BaseModel):
    pass

class CRUDMovimentacao(CRUDBase[Movimentacao, MovimentacaoCreate, MovimentacaoUpdate]):
    async def get_by_asset(self, db: AsyncSession, asset_id: int) -> List[Movimentacao]:
        result = await db.execute(select(Movimentacao).filter(Movimentacao.asset_id == asset_id).order_by(Movimentacao.data.desc()))
        return result.scalars().all()

from datetime import datetime
from app.models.asset import Asset, AssetStatus
from app.models.transaction import TipoMovimentacao

class CRUDSolicitacao(CRUDBase[Solicitacao, SolicitacaoCreate, SolicitacaoUpdate]):
    async def get_multi(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Solicitacao]:
        """Override to include eager loading of relationships"""
        result = await db.execute(
            select(Solicitacao)
            .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
            .offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def get_pending(self, db: AsyncSession) -> List[Solicitacao]:
        result = await db.execute(
            select(Solicitacao)
            .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
            .filter(Solicitacao.status == StatusSolicitacao.PENDENTE)
        )
        return result.scalars().all()
    
    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Solicitacao]:
        result = await db.execute(
            select(Solicitacao)
            .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
            .filter(Solicitacao.solicitante_id == user_id)
        )
        return result.scalars().all()

    async def approve(self, db: AsyncSession, *, solicitacao_id: int, aprovador_id: int) -> Solicitacao | None:
        solicitacao = await self.get(db, solicitacao_id)
        if not solicitacao or solicitacao.status != StatusSolicitacao.PENDENTE:
            return None

        # 1. Update Solicitation
        solicitacao.status = StatusSolicitacao.APROVADA
        solicitacao.aprovador_id = aprovador_id
        solicitacao.data_aprovacao = datetime.utcnow()

        # 2. Update Asset
        asset = await db.scalar(select(Asset).filter(Asset.id == solicitacao.asset_id))
        if asset:
            asset.status = AssetStatus.EM_USO
            asset.current_user_id = solicitacao.solicitante_id
            db.add(asset)

            # 3. Create Movement
            movimentacao = Movimentacao(
                asset_id=asset.id,
                tipo=TipoMovimentacao.EMPRESTIMO,
                de_user_id=aprovador_id, # Manager who approved
                para_user_id=solicitacao.solicitante_id,
                data=datetime.utcnow(),
                observacao=f"Solicitação {solicitacao.id} aprovada."
            )
            db.add(movimentacao)

        db.add(solicitacao)
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao

    async def reject(self, db: AsyncSession, *, solicitacao_id: int, aprovador_id: int) -> Solicitacao | None:
        solicitacao = await self.get(db, solicitacao_id)
        if not solicitacao or solicitacao.status != StatusSolicitacao.PENDENTE:
            return None

        solicitacao.status = StatusSolicitacao.REJEITADA
        solicitacao.aprovador_id = aprovador_id
        solicitacao.data_aprovacao = datetime.utcnow()
        
        db.add(solicitacao)
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao

movimentacao = CRUDMovimentacao(Movimentacao)
solicitacao = CRUDSolicitacao(Solicitacao)
