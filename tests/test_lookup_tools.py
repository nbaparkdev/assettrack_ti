import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai_assistant.tools import (
    list_departments, list_locations, list_categories, list_suppliers, search_users, read_system_manual, clean_unwanted_tool_tags
)
from app.models.location import Departamento, Localizacao
from app.models.asset_category import AssetCategory
from app.models.supplier import Fornecedor
from app.models.user import User

@pytest.mark.asyncio
async def test_lookup_tools(db_session: AsyncSession):
    # 1. Create seed data
    dep = Departamento(nome="TI")
    db_session.add(dep)
    await db_session.commit()
    await db_session.refresh(dep)

    loc = Localizacao(nome="Sala de Redes", departamento_id=dep.id)
    cat = AssetCategory(nome="Computadores", descricao="Notebooks e Desktops")
    sup = Fornecedor(nome="Distribuidora de TI", cnpj="12.345.678/0001-99")
    db_session.add_all([loc, cat, sup])
    await db_session.commit()

    # 2. Test list_departments
    res_deps = await list_departments(db=db_session, user_id=1)
    assert "TI" in res_deps

    # 3. Test list_locations
    res_locs = await list_locations(db=db_session, user_id=1)
    assert "Sala de Redes" in res_locs

    # 4. Test list_categories
    res_cats = await list_categories(db=db_session, user_id=1)
    assert "Computadores" in res_cats

    # 5. Test list_suppliers
    res_sups = await list_suppliers(db=db_session, user_id=1)
    assert "Distribuidora de TI" in res_sups

    # 6. Test search_users (should be empty initially, then match)
    res_users = await search_users(db=db_session, user_id=1, query="Inexistente")
    assert "Nenhum usuário encontrado" in res_users

    # 7. Test read_system_manual
    res_manual = await read_system_manual(db=db_session, user_id=1, document_name="manual_do_usuario")
    assert "Manual" in res_manual or "AssetTrack" in res_manual

    # 8. Test clean_unwanted_tool_tags
    dirty_text = "Manutenções: Há [get_maintenance_report {} - Number of pending orders] ativas."
    cleaned = clean_unwanted_tool_tags(dirty_text)
    assert "get_maintenance_report" not in cleaned
    assert "Number of pending" not in cleaned
    assert "[" not in cleaned and "]" not in cleaned
