# app/crud/crud_invoice.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import NotaFiscal
from app.schemas.invoice import NotaFiscalCreate, NotaFiscalUpdate


async def get_nota_fiscal(db: AsyncSession, nota_fiscal_id: int) -> NotaFiscal | None:
    result = await db.execute(select(NotaFiscal).filter(NotaFiscal.id == nota_fiscal_id))
    return result.scalars().first()

async def get_nota_fiscal_by_numero(db: AsyncSession, numero_nota: str) -> NotaFiscal | None:
    result = await db.execute(select(NotaFiscal).filter(NotaFiscal.numero_nota == numero_nota))
    return result.scalars().first()

async def get_notas_fiscais(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[NotaFiscal]:
    result = await db.execute(select(NotaFiscal).offset(skip).limit(limit))
    return result.scalars().all()

async def create_nota_fiscal(db: AsyncSession, nota_fiscal: NotaFiscalCreate) -> NotaFiscal:
    db_nota_fiscal = NotaFiscal(**nota_fiscal.model_dump())
    db.add(db_nota_fiscal)
    await db.commit()
    await db.refresh(db_nota_fiscal)
    return db_nota_fiscal

async def update_nota_fiscal(db: AsyncSession, db_nota_fiscal: NotaFiscal, nota_fiscal: NotaFiscalUpdate) -> NotaFiscal:
    update_data = nota_fiscal.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_nota_fiscal, key, value)
    await db.commit()
    await db.refresh(db_nota_fiscal)
    return db_nota_fiscal

async def delete_nota_fiscal(db: AsyncSession, db_nota_fiscal: NotaFiscal) -> NotaFiscal:
    await db.delete(db_nota_fiscal)
    await db.commit()
    return db_nota_fiscal
