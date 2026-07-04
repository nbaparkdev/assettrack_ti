from abc import ABC, abstractmethod
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

class LLMBaseService(ABC):
    @abstractmethod
    async def chat(self, db: AsyncSession, user_id: int, messages: List[Dict[str, Any]], allow_advanced_tools: bool = False) -> str:
        """
        Recebe um histórico de mensagens e retorna a resposta do assistente (string).
        Lida internamente com chamadas de função (Function Calling) se necessário.
        """
        pass
