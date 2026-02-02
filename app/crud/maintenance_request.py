
# app/crud/maintenance_request.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.core.datetime_utils import now_sp

from app.crud.base import CRUDBase
from app.models.maintenance_request import SolicitacaoManutencao, StatusSolicitacaoManutencao
from app.models.maintenance import Manutencao, TipoManutencao, StatusManutencao
from app.models.asset import Asset, AssetStatus
from app.schemas.maintenance_request import SolicitacaoManutencaoCreate, SolicitacaoManutencaoUpdate


class CRUDMaintenanceRequest(CRUDBase[SolicitacaoManutencao, SolicitacaoManutencaoCreate, SolicitacaoManutencaoUpdate]):
    
    async def create_request(
        self, 
        db: AsyncSession, 
        *, 
        obj_in: SolicitacaoManutencaoCreate,
        solicitante_id: int
    ) -> SolicitacaoManutencao:
        """Cria nova solicitação de manutenção"""
        db_obj = SolicitacaoManutencao(
            asset_id=obj_in.asset_id,
            solicitante_id=solicitante_id,
            descricao=obj_in.descricao,
            prioridade=obj_in.prioridade,
            status=StatusSolicitacaoManutencao.PENDENTE
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_with_relations(
        self, 
        db: AsyncSession, 
        *, 
        id: int
    ) -> Optional[SolicitacaoManutencao]:
        """Busca solicitação com relacionamentos carregados"""
        result = await db.execute(
            select(SolicitacaoManutencao)
            .options(
                selectinload(SolicitacaoManutencao.solicitante),
                selectinload(SolicitacaoManutencao.responsavel),
                selectinload(SolicitacaoManutencao.asset),
                selectinload(SolicitacaoManutencao.manutencao)
            )
            .filter(SolicitacaoManutencao.id == id)
        )
        return result.scalar_one_or_none()
    
    async def list_pending(
        self, 
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[SolicitacaoManutencao]:
        """Lista solicitações pendentes (para técnicos/gerentes)"""
        result = await db.execute(
            select(SolicitacaoManutencao)
            .options(
                selectinload(SolicitacaoManutencao.solicitante),
                selectinload(SolicitacaoManutencao.asset)
            )
            .filter(SolicitacaoManutencao.status == StatusSolicitacaoManutencao.PENDENTE)
            .order_by(SolicitacaoManutencao.data_solicitacao.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def list_all(
        self, 
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[SolicitacaoManutencao]:
        """Lista todas as solicitações (para técnicos/gerentes)"""
        result = await db.execute(
            select(SolicitacaoManutencao)
            .options(
                selectinload(SolicitacaoManutencao.solicitante),
                selectinload(SolicitacaoManutencao.asset),
                selectinload(SolicitacaoManutencao.responsavel)
            )
            .order_by(SolicitacaoManutencao.data_solicitacao.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def list_by_user(
        self, 
        db: AsyncSession, 
        *, 
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SolicitacaoManutencao]:
        """Lista solicitações de um usuário específico"""
        result = await db.execute(
            select(SolicitacaoManutencao)
            .options(
                selectinload(SolicitacaoManutencao.asset),
                selectinload(SolicitacaoManutencao.responsavel)
            )
            .filter(SolicitacaoManutencao.solicitante_id == user_id)
            .order_by(SolicitacaoManutencao.data_solicitacao.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def accept_request(
        self, 
        db: AsyncSession, 
        *, 
        request_id: int,
        responsavel_id: int,
        observacao: Optional[str] = None
    ) -> Optional[SolicitacaoManutencao]:
        """
        Aceita uma solicitação e cria a manutenção correspondente.
        Muda status do asset para MANUTENCAO.
        """
        solicitacao = await self.get_with_relations(db, id=request_id)
        if not solicitacao:
            return None
        
        if solicitacao.status != StatusSolicitacaoManutencao.PENDENTE:
            return None
        
        # Criar Manutenção
        manutencao = Manutencao(
            asset_id=solicitacao.asset_id,
            responsavel_id=responsavel_id,
            motivo=solicitacao.descricao,
            tipo=TipoManutencao.CORRETIVA,
            status=StatusManutencao.EM_ANDAMENTO
        )
        db.add(manutencao)
        await db.flush()  # Get manutencao.id
        
        # Atualizar solicitação
        solicitacao.status = StatusSolicitacaoManutencao.EM_ANDAMENTO
        solicitacao.responsavel_id = responsavel_id
        solicitacao.data_resposta = now_sp()
        solicitacao.observacao_resposta = observacao
        solicitacao.manutencao_id = manutencao.id
        
        # Mudar status do asset
        asset = await db.get(Asset, solicitacao.asset_id)
        if asset:
            asset.status = AssetStatus.MANUTENCAO
        
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao
    
    async def reject_request(
        self, 
        db: AsyncSession, 
        *, 
        request_id: int,
        responsavel_id: int,
        observacao: str
    ) -> Optional[SolicitacaoManutencao]:
        """Rejeita uma solicitação com justificativa"""
        solicitacao = await self.get(db, id=request_id)
        if not solicitacao:
            return None
        
        if solicitacao.status != StatusSolicitacaoManutencao.PENDENTE:
            return None
        
        solicitacao.status = StatusSolicitacaoManutencao.REJEITADA
        solicitacao.responsavel_id = responsavel_id
        solicitacao.data_resposta = now_sp()
        solicitacao.observacao_resposta = observacao
        
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao
    
    async def complete_maintenance(
        self, 
        db: AsyncSession, 
        *, 
        request_id: int,
        observacao_conclusao: Optional[str] = None
    ) -> Optional[SolicitacaoManutencao]:
        """
        Técnico marca a manutenção como concluída.
        Status muda para AGUARDANDO_ENTREGA.
        O usuário ainda precisa confirmar o recebimento.
        """
        solicitacao = await self.get_with_relations(db, id=request_id)
        if not solicitacao:
            return None
        
        if solicitacao.status != StatusSolicitacaoManutencao.EM_ANDAMENTO:
            return None
        
        # Atualizar solicitação
        solicitacao.status = StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA
        solicitacao.data_conclusao_tecnico = now_sp()
        if observacao_conclusao:
            solicitacao.observacao_resposta = observacao_conclusao
        
        # Atualizar manutenção
        if solicitacao.manutencao:
            solicitacao.manutencao.status = StatusManutencao.CONCLUIDA
            solicitacao.manutencao.data_conclusao = now_sp()
            solicitacao.manutencao.observacao_conclusao = observacao_conclusao
        
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao
    
    async def confirm_delivery(
        self, 
        db: AsyncSession, 
        *, 
        request_id: int,
        user_id: int
    ) -> Optional[SolicitacaoManutencao]:
        """
        Usuário confirma recebimento do ativo após manutenção.
        Status muda para CONCLUIDA e ativo volta para status ATIVO.
        """
        solicitacao = await self.get_with_relations(db, id=request_id)
        if not solicitacao:
            return None
        
        # Verificar se é o solicitante original
        if solicitacao.solicitante_id != user_id:
            return None
        
        if solicitacao.status != StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA:
            return None
        
        # Atualizar solicitação
        solicitacao.status = StatusSolicitacaoManutencao.CONCLUIDA
        solicitacao.data_entrega = now_sp()
        
        # Atualizar status do asset para EM_USO (entregue ao usuário)
        asset = await db.get(Asset, solicitacao.asset_id)
        if asset:
            asset.status = AssetStatus.EM_USO
            asset.current_user_id = solicitacao.solicitante_id
        
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao
    
    async def list_awaiting_delivery(
        self, 
        db: AsyncSession,
        *,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[SolicitacaoManutencao]:
        """Lista solicitações aguardando confirmação de entrega para um usuário"""
        result = await db.execute(
            select(SolicitacaoManutencao)
            .options(
                selectinload(SolicitacaoManutencao.asset),
                selectinload(SolicitacaoManutencao.responsavel)
            )
            .filter(
                SolicitacaoManutencao.solicitante_id == user_id,
                SolicitacaoManutencao.status.in_([
                    StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA,
                    StatusSolicitacaoManutencao.ENTREGUE
                ])
            )
            .order_by(SolicitacaoManutencao.data_conclusao_tecnico.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def confirm_delivery_by_tech(
        self, 
        db: AsyncSession, 
        *, 
        request_id: int,
        tech_id: int,
        observation: Optional[str] = None
    ) -> Optional[SolicitacaoManutencao]:
        """
        Técnico confirma entrega após validar QR do usuário.
        Status muda para CONCLUIDA e ativo volta para DISPONIVEL.
        """
        solicitacao = await self.get_with_relations(db, id=request_id)
        if not solicitacao:
            return None
        
        if solicitacao.status != StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA:
            return None
        
        # Atualizar solicitação
        solicitacao.status = StatusSolicitacaoManutencao.ENTREGUE
        solicitacao.data_entrega = now_sp()
        if observation:
            solicitacao.observacao_resposta = observation
        
        # Atualizar status do asset para EM_USO (entregue ao usuário)
        asset = await db.get(Asset, solicitacao.asset_id)
        if asset:
            asset.status = AssetStatus.EM_USO
            asset.current_user_id = solicitacao.solicitante_id
        
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao

    async def confirm_receipt_by_user(
        self,
        db: AsyncSession,
        *,
        request_id: int,
        user_id: int
    ) -> Optional[SolicitacaoManutencao]:
        """
        Usuário confirma que recebeu o ativo e que está tudo ok.
        Status muda de ENTREGUE para CONCLUIDA.
        """
        solicitacao = await self.get_with_relations(db, id=request_id)
        if not solicitacao:
            return None
            
        if solicitacao.solicitante_id != user_id:
            return None
            
        if solicitacao.status != StatusSolicitacaoManutencao.ENTREGUE:
            return None
            
        solicitacao.status = StatusSolicitacaoManutencao.CONCLUIDA
        # Data de entrega já foi setada quando o técnico entregou (ENTREGUE)
        
        await db.commit()
        await db.refresh(solicitacao)
        return solicitacao
    
    async def list_by_user_and_status(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        status: StatusSolicitacaoManutencao,
        skip: int = 0,
        limit: int = 20
    ) -> List[SolicitacaoManutencao]:
        """Lista solicitações de um usuário com status específico"""
        result = await db.execute(
            select(SolicitacaoManutencao)
            .options(
                selectinload(SolicitacaoManutencao.asset),
                selectinload(SolicitacaoManutencao.solicitante)
            )
            .filter(
                SolicitacaoManutencao.solicitante_id == user_id,
                SolicitacaoManutencao.status == status
            )
            .order_by(SolicitacaoManutencao.data_solicitacao.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_reports(
        self,
        db: AsyncSession,
        *,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[StatusSolicitacaoManutencao] = None,
        responsavel_id: Optional[int] = None,
        asset_id: Optional[int] = None,
        limit: int = 200
    ) -> List[SolicitacaoManutencao]:
        """Gera relatório de manutenções com filtros"""
        query = select(SolicitacaoManutencao).options(
            selectinload(SolicitacaoManutencao.asset),
            selectinload(SolicitacaoManutencao.solicitante),
            selectinload(SolicitacaoManutencao.responsavel),
            selectinload(SolicitacaoManutencao.manutencao)
        )
        
        # Filtros
        if start_date:
            query = query.filter(SolicitacaoManutencao.data_solicitacao >= start_date)
        
        if end_date:
            query = query.filter(SolicitacaoManutencao.data_solicitacao <= end_date)
            
        if status:
            query = query.filter(SolicitacaoManutencao.status == status)
            
        if responsavel_id:
            query = query.filter(SolicitacaoManutencao.responsavel_id == responsavel_id)
            
        if asset_id:
            query = query.filter(SolicitacaoManutencao.asset_id == asset_id)
            
        # Ordenação: mais recentes primeiro
        query = query.order_by(SolicitacaoManutencao.data_solicitacao.desc())
        
        if limit > 0:
            query = query.limit(limit)
            
        result = await db.execute(query)
        return list(result.scalars().all())


maintenance_request = CRUDMaintenanceRequest(SolicitacaoManutencao)

