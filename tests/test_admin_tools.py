import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.ai_assistant.tools import (
    create_asset, update_asset, deactivate_asset,
    update_ticket_status, create_maintenance, complete_maintenance,
    create_user, deactivate_user
)
from app.models.asset import Asset, AssetStatus
from app.models.user import User, UserRole
from app.models.transaction import Solicitacao, StatusSolicitacao
from app.models.maintenance import Manutencao, StatusManutencao

@pytest.mark.asyncio
async def test_admin_tools_crud(db_session: AsyncSession):
    # 1. Create User
    res_user = await create_user(
        db=db_session,
        user_id=1,
        email="tecnico@exemplo.com",
        nome="Técnico Teste",
        role="tecnico",
        matricula="MTR-123",
        cargo="Suporte"
    )
    assert "cadastrado com sucesso" in res_user

    user = (await db_session.execute(select(User).where(User.email == "tecnico@exemplo.com"))).scalar_one()
    assert user.nome == "Técnico Teste"
    assert user.role == UserRole.TECNICO
    assert user.is_active is True

    # 2. Deactivate User
    res_deact = await deactivate_user(
        db=db_session,
        user_id=1,
        user_to_deactivate_id=user.id
    )
    assert "desativado com sucesso" in res_deact
    assert user.is_active is False

    # 3. Create Asset
    res_asset = await create_asset(
        db=db_session,
        user_id=1,
        nome="Dell Latitude 3420",
        e_patrimonio="PAT-888999",
        modelo="Latitude",
        valor=4500.0,
        status="Disponível"
    )
    assert "cadastrado com sucesso" in res_asset
    
    asset = (await db_session.execute(select(Asset).where(Asset.e_patrimonio == "PAT-888999"))).scalar_one()
    assert asset.nome == "Dell Latitude 3420"
    assert asset.status == AssetStatus.DISPONIVEL

    # 4. Update Asset
    res_up_asset = await update_asset(
        db=db_session,
        user_id=1,
        asset_id=asset.id,
        nome="Dell Latitude Editado",
        status="Armazenado"
    )
    assert "atualizado com sucesso" in res_up_asset
    assert asset.nome == "Dell Latitude Editado"
    assert asset.status == AssetStatus.ARMAZENADO

    # 5. Create Maintenance OS
    res_maint = await create_maintenance(
        db=db_session,
        user_id=1,
        asset_id=asset.id,
        motivo="Tela piscando"
    )
    assert "aberta com sucesso" in res_maint
    assert asset.status == AssetStatus.MANUTENCAO

    os = (await db_session.execute(select(Manutencao).where(Manutencao.asset_id == asset.id))).scalar_one()
    assert os.status == StatusManutencao.EM_ANDAMENTO

    # 6. Complete OS
    res_comp_maint = await complete_maintenance(
        db=db_session,
        user_id=1,
        os_id=os.id,
        observacao_conclusao="Troca de display",
        custo=350.0
    )
    assert "concluída com sucesso" in res_comp_maint
    assert os.status == StatusManutencao.CONCLUIDA
    assert asset.status == AssetStatus.DISPONIVEL

    # 7. Deactivate Asset
    res_deact_asset = await deactivate_asset(
        db=db_session,
        user_id=1,
        asset_id=asset.id
    )
    assert "desativado com sucesso" in res_deact_asset
    assert asset.status == AssetStatus.BAIXADO
    assert asset.bloqueado is True
