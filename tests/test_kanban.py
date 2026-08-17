# tests/test_kanban.py
import pytest

from app.crud.kanban import crud_kanban
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_kanban_crud_workflow(db_session):
    # 1. Create creator and user
    creator = User(
        email="kanban_admin@test.com",
        hashed_password="hash",
        nome="Kanban Admin",
        role=UserRole.ADMIN,
        is_active=True
    )
    user = User(
        email="kanban_user@test.com",
        hashed_password="hash",
        nome="Kanban Member",
        role=UserRole.USUARIO,
        is_active=True
    )
    db_session.add(creator)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(creator)
    await db_session.refresh(user)

    # 2. Initially usuario_comum has 0 active projects
    count = await crud_kanban.count_user_active_projects(db_session, user)
    assert count == 0

    # 3. Create project with default columns and add member
    project = await crud_kanban.create_project(
        db=db_session,
        titulo="Projeto Infraestrutura",
        descricao="Migração de rede",
        criador_id=creator.id,
        participant_ids=[user.id]
    )
    assert project.id is not None
    assert len(project.colunas) == 4
    assert any(c.nome == "A Fazer" for c in project.colunas)

    # 4. Member now has 1 active project
    count_after = await crud_kanban.count_user_active_projects(db_session, user)
    assert count_after == 1

    # 5. Create a card
    first_col = project.colunas[0]
    card = await crud_kanban.create_card(
        db=db_session,
        project_id=project.id,
        column_id=first_col.id,
        titulo="Comprar Switches",
        descricao="Cotação de switches gerenciáveis",
        criador_id=creator.id,
        responsavel_id=user.id,
        assignee_ids=[user.id],
        asset_ids=[],
        prioridade="alta"
    )
    assert card.id is not None
    assert card.prioridade == "alta"

    # 6. Move card to next column
    second_col = project.colunas[1]
    moved_card = await crud_kanban.move_card(
        db=db_session,
        card_id=card.id,
        target_column_id=second_col.id,
        target_order=0
    )
    assert moved_card.column_id == second_col.id

    # 7. Add attachment
    attachment = await crud_kanban.add_attachment(
        db=db_session,
        card_id=card.id,
        nome="Especificação Técnica",
        tipo="link",
        url="https://wiki.test.com/switch-spec"
    )
    assert attachment.id is not None
    assert attachment.tipo == "link"

    # 8. Get project board
    loaded_project = await crud_kanban.get_project_by_id(db_session, project.id)
    assert loaded_project is not None
    assert len(loaded_project.colunas) == 4

@pytest.mark.asyncio
async def test_kanban_procurement_and_stock_linking(db_session):
    from app.models.location import Departamento
    from app.models.procurement import (
        CostCenter,
        MaterialStock,
        ProductType,
        PurchaseCategory,
        PurchaseProduct,
        PurchaseRequest,
        PurchaseRequestStatus,
    )

    # 1. Create base data
    dept = Departamento(nome="TI Infra")
    db_session.add(dept)
    cat = PurchaseCategory(nome="Equipamentos", ativo=True)
    db_session.add(cat)
    cc = CostCenter(codigo="CC-TI-TEST", nome="Centro Teste TI")
    db_session.add(cc)
    await db_session.commit()
    await db_session.refresh(dept)
    await db_session.refresh(cat)
    await db_session.refresh(cc)

    prod = PurchaseProduct(
        codigo="PROD-TEST-1",
        nome="Switch 24p Gigabit",
        categoria_id=cat.id,
        tipo=ProductType.EQUIPAMENTO,
        unidade="UN",
        ativo=True
    )
    db_session.add(prod)
    await db_session.commit()
    await db_session.refresh(prod)

    stock = MaterialStock(product_id=prod.id, quantidade_saldo=10.0)
    db_session.add(stock)

    user = User(
        email="kb_proc_user@test.com",
        hashed_password="hash",
        nome="Admin Proc",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(stock)

    # 2. Create project and card
    project = await crud_kanban.create_project(
        db=db_session,
        titulo="Projeto Rede Wifi",
        descricao="Deploy APs",
        criador_id=user.id,
        participant_ids=[user.id]
    )
    col = project.colunas[0]
    card = await crud_kanban.create_card(
        db=db_session,
        project_id=project.id,
        column_id=col.id,
        titulo="Instalar AP 1",
        descricao="Cabo Cat6",
        criador_id=user.id,
        responsavel_id=user.id,
        assignee_ids=[user.id],
        asset_ids=[]
    )

    # 3. Create purchase request linked to card
    req = PurchaseRequest(
        numero="SC-2026-000099",
        solicitante_id=user.id,
        departamento_id=dept.id,
        centro_custo_id=cc.id,
        justificativa="Compra de AP para projeto",
        status=PurchaseRequestStatus.PENDENTE
    )
    db_session.add(req)
    await db_session.commit()
    await db_session.refresh(req)

    card.purchase_request_id = req.id
    card.tipo_item_necessario = "Imobilizado"
    await db_session.commit()

    # 4. Verify link
    target_card = await crud_kanban.get_card_by_id(db_session, card.id)
    assert target_card is not None
    assert target_card.purchase_request_id == req.id
    assert target_card.purchase_request.numero == "SC-2026-000099"
    assert target_card.tipo_item_necessario == "Imobilizado"

    # 5. Link stock item to card
    card.material_stock_id = stock.id
    card.tipo_item_necessario = "Estoque"
    await db_session.commit()

    target_card2 = await crud_kanban.get_card_by_id(db_session, card.id)
    assert target_card2 is not None
    assert target_card2.material_stock_id == stock.id
    assert target_card2.material_stock.quantidade_saldo == 10.0

