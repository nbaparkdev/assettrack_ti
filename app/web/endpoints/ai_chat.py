from typing import Annotated, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.web.dependencies import get_active_user_web
from app.models.user import User
from app.crud.system_settings import system_settings
from app.services.ai_assistant.llm_factory import get_llm_service

router = APIRouter()

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]

class ChatResponse(BaseModel):
    response: str

@router.post("/api/v1/chat", response_model=ChatResponse)
async def ai_chat_endpoint(
    request: ChatRequest,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ai_enabled_str = await system_settings.get_setting(db, "ai_enabled", default_value="false")
    if ai_enabled_str.lower() != "true":
        raise HTTPException(status_code=403, detail="Assistente IA desativado")
        
    ai_provider = await system_settings.get_setting(db, "ai_provider", default_value="openai")
    api_key_field = f"{ai_provider}_api_key"
    api_key = await system_settings.get_setting(db, api_key_field, default_value="")
    
    model_field = f"{ai_provider}_model"
    model_name = await system_settings.get_setting(db, model_field, default_value="")
    
    if not api_key:
        raise HTTPException(status_code=500, detail=f"Chave de API não configurada para {ai_provider}")
        
    ai_advanced_str = await system_settings.get_setting(db, "ai_advanced_functions", default_value="false")
    allow_advanced = (ai_advanced_str.lower() == "true")
    
    try:
        llm_service = get_llm_service(provider=ai_provider, api_key=api_key, model_name=model_name)
        response_text = await llm_service.chat(db=db, user_id=current_user.id, messages=request.messages, allow_advanced_tools=allow_advanced)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
