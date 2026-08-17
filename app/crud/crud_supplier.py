# app/crud/crud_supplier.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Fornecedor
from app.schemas.supplier import FornecedorCreate, FornecedorUpdate


async def get_fornecedor(db: AsyncSession, fornecedor_id: int) -> Fornecedor | None:
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Fornecedor)
        .options(selectinload(Fornecedor.notas_fiscais))
        .filter(Fornecedor.id == fornecedor_id)
    )
    return result.scalars().first()

async def get_fornecedores(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Fornecedor]:
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(Fornecedor)
        .options(selectinload(Fornecedor.notas_fiscais))
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

async def get_fornecedor_by_nome(db: AsyncSession, nome: str) -> Fornecedor | None:
    result = await db.execute(select(Fornecedor).filter(Fornecedor.nome == nome))
    return result.scalars().first()

async def create_fornecedor(db: AsyncSession, fornecedor: FornecedorCreate) -> Fornecedor:
    db_fornecedor = Fornecedor(**fornecedor.model_dump())
    db.add(db_fornecedor)
    await db.commit()
    await db.refresh(db_fornecedor)
    return db_fornecedor

async def update_fornecedor(db: AsyncSession, db_fornecedor: Fornecedor, fornecedor: FornecedorUpdate) -> Fornecedor:
    update_data = fornecedor.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_fornecedor, key, value)
    await db.commit()
    await db.refresh(db_fornecedor)
    return db_fornecedor

async def delete_fornecedor(db: AsyncSession, fornecedor_id: int) -> None:
    fornecedor = await get_fornecedor(db, fornecedor_id)
    if fornecedor:
        await db.delete(fornecedor)
        await db.commit()
