# app/services/qr_log_service.py
"""
Serviço para registro de logs de uso do QR Code.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.qr_log import QRLog, QRLogAction
from fastapi import Request


class QRLogService:
    """Serviço para registrar ações de QR Code"""
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extrai o IP do cliente da requisição"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user_id: int,
        action: QRLogAction,
        request: Request = None,
        actor_id: int = None,
        details: str = None,
        success: bool = True
    ) -> QRLog:
        """
        Registra uma ação de QR Code no banco de dados.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do dono do QR Code
            action: Tipo de ação
            request: Request FastAPI para extrair IP
            actor_id: ID de quem executou (se diferente do dono)
            details: Detalhes adicionais
            success: Se a ação foi bem sucedida
        """
        ip_address = None
        if request:
            ip_address = QRLogService.get_client_ip(request)
        
        log_entry = QRLog(
            user_id=user_id,
            actor_id=actor_id,
            action=action,
            ip_address=ip_address,
            details=details,
            success=success
        )
        
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        
        return log_entry
    
    @staticmethod
    async def log_login(db: AsyncSession, user_id: int, request: Request, success: bool = True):
        """Log de login via QR"""
        action = QRLogAction.LOGIN if success else QRLogAction.LOGIN_FAILED
        return await QRLogService.log_action(
            db=db,
            user_id=user_id,
            action=action,
            request=request,
            success=success
        )
    
    @staticmethod
    async def log_regenerate(db: AsyncSession, user_id: int, request: Request):
        """Log de regeneração de token"""
        return await QRLogService.log_action(
            db=db,
            user_id=user_id,
            action=QRLogAction.REGENERATE,
            request=request
        )
    
    @staticmethod
    async def log_pin_action(db: AsyncSession, user_id: int, request: Request, is_change: bool = False):
        """Log de configuração/alteração de PIN"""
        action = QRLogAction.PIN_CHANGED if is_change else QRLogAction.PIN_SET
        return await QRLogService.log_action(
            db=db,
            user_id=user_id,
            action=action,
            request=request
        )
    
    @staticmethod
    async def log_profile_view(db: AsyncSession, user_id: int, actor_id: int, request: Request):
        """Log de consulta de perfil via QR"""
        return await QRLogService.log_action(
            db=db,
            user_id=user_id,
            action=QRLogAction.PROFILE_VIEW,
            request=request,
            actor_id=actor_id
        )
    
    @staticmethod
    async def log_delivery_confirm(
        db: AsyncSession, 
        user_id: int, 
        actor_id: int, 
        request: Request,
        solicitacao_id: int = None
    ):
        """Log de confirmação de entrega via QR"""
        details = f"solicitacao_id:{solicitacao_id}" if solicitacao_id else None
        return await QRLogService.log_action(
            db=db,
            user_id=user_id,
            action=QRLogAction.DELIVERY_CONFIRM,
            request=request,
            actor_id=actor_id,
            details=details
        )
