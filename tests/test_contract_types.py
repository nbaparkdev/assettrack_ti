import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.procurement import ContractType, PurchaseContract
from app.schemas.procurement import ContractTypeCreate, ContractTypeUpdate, PurchaseContractCreate
from app.crud import procurement as crud_proc
from datetime import datetime

@pytest.mark.asyncio
async def test_crud_contract_type(db_session: AsyncSession):
    # 1. Create a new contract type
    ct_in = ContractTypeCreate(
        nome="Licenciamento SaaS",
        descricao="Contratos de licenças de software em nuvem",
        ativo=True
    )
    
    ct = await crud_proc.create_contract_type(db_session, ct_in)
    assert ct.id is not None
    assert ct.nome == "Licenciamento SaaS"
    assert ct.descricao == "Contratos de licenças de software em nuvem"
    assert ct.ativo is True

    # 2. Get the contract type
    db_ct = await crud_proc.get_contract_type(db_session, ct.id)
    assert db_ct is not None
    assert db_ct.nome == "Licenciamento SaaS"

    # 3. Get all contract types
    types = await crud_proc.get_contract_types(db_session)
    assert len(types) >= 1
    assert any(t.nome == "Licenciamento SaaS" for t in types)

    # 4. Update the contract type
    ct_up = ContractTypeUpdate(
        nome="Licenciamento SaaS Pro",
        descricao="Contratos de software SaaS corporativo",
        ativo=False
    )
    updated_ct = await crud_proc.update_contract_type(db_session, db_ct, ct_up)
    assert updated_ct.nome == "Licenciamento SaaS Pro"
    assert updated_ct.descricao == "Contratos de software SaaS corporativo"
    assert updated_ct.ativo is False

    # Get active-only types
    active_types = await crud_proc.get_contract_types(db_session, only_active=True)
    assert not any(t.id == ct.id for t in active_types)

    # 5. Delete the contract type
    success = await crud_proc.delete_contract_type(db_session, ct.id)
    assert success is True

    deleted_ct = await crud_proc.get_contract_type(db_session, ct.id)
    assert deleted_ct is None
