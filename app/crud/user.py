
# app/crud/user.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    async def get_by_qr_token(self, db: AsyncSession, *, token: str) -> Optional[User]:
        """Busca usuário pelo token QR"""
        result = await db.execute(select(User).filter(User.qr_token == token))
        return result.scalars().first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=pwd_context.hash(obj_in.password),
            nome=obj_in.nome,
            matricula=obj_in.matricula,
            cargo=obj_in.cargo,
            role=obj_in.role,
            is_active=obj_in.is_active,
            departamento_id=obj_in.departamento_id
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def regenerate_qr_token(self, db: AsyncSession, *, user_id: int) -> str:
        """Gera novo token QR para o usuário, invalidando o anterior"""
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise ValueError("Usuário não encontrado")
        
        new_token = str(uuid.uuid4())
        user.qr_token = new_token
        user.qr_token_created_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return new_token

    async def set_pin(self, db: AsyncSession, *, user_id: int, pin: str) -> bool:
        """Define PIN para login via QR Code"""
        if not pin or len(pin) < 4 or len(pin) > 6 or not pin.isdigit():
            raise ValueError("PIN deve ter 4-6 dígitos numéricos")
        
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if not user:
            raise ValueError("Usuário não encontrado")
        
        user.pin_hash = pwd_context.hash(pin)
        await db.commit()
        return True

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def verify_pin(self, plain_pin: str, pin_hash: str) -> bool:
        """Verifica se o PIN está correto"""
        if not pin_hash:
            return False
        return pwd_context.verify(plain_pin, pin_hash)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

user = CRUDUser(User)

