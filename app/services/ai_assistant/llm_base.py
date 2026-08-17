from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class LLMBaseService(ABC):
    @abstractmethod
    async def chat(
        self, 
        db: AsyncSession, 
        user_id: int, 
        messages: list[dict[str, Any]], 
        allow_advanced_tools: bool = False,
        user_context: dict[str, str] | None = None
    ) -> str:
        """
        Recebe um histórico de mensagens e retorna a resposta do assistente (string).
        Lida internamente com chamadas de função (Function Calling) se necessário.
        user_context contém nome, role e email do usuário logado.
        """
