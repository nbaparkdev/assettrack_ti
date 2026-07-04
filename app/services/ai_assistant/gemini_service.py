import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai
from google.generativeai.types import content_types

from app.services.ai_assistant.llm_base import LLMBaseService
from app.services.ai_assistant.tools import AVAILABLE_TOOLS, execute_tool

def get_gemini_tools_schema():
    declarations = []
    for name, metadata in AVAILABLE_TOOLS.items():
        declarations.append({
            "name": name,
            "description": metadata["description"],
            # Simplify mapping, empty params for now
        })
    return declarations

class GeminiService(LLMBaseService):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash-latest"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model,
            system_instruction="Você é o assistente virtual do AssetTrack TI. Ajude os usuários a gerenciar ativos e chamados de forma concisa."
        )
        
        # Tools in Gemini are usually passed as Python callables if using the SDK, 
        # but since ours are async and take db/user_id, we map them conceptually.
        # For this prototype, we'll implement a simple text chat and rely on manual tool mapping 
        # if the user specifically requests tool execution. 
        # Alternatively, we just pass the names and descriptions and let Gemini respond with JSON if needed,
        # but the standard way is to define FunctionDeclarations.
        # To avoid complex SDK versioning issues, we wrap it simply.
        
    async def chat(self, db: AsyncSession, user_id: int, messages: List[Dict[str, Any]], allow_advanced_tools: bool = False) -> str:
        # Convert OpenAI format messages to Gemini format
        history = []
        for msg in messages:
            if msg["role"] == "system":
                continue # Handled in system_instruction
            role = "user" if msg["role"] == "user" else "model"
            history.append({"role": role, "parts": [msg["content"]]})
        
        # Start chat
        chat_session = self.model.start_chat(history=history[:-1])
        
        last_user_message = history[-1]["parts"][0]
        
        try:
            # We aren't attaching formal tools here due to SDK complex tool format mapping 
            # for async injected functions, but in a full implementation we would use:
            # response = chat_session.send_message(last_user_message, tools=[...])
            response = chat_session.send_message(last_user_message)
            return response.text
        except Exception as e:
            return f"Erro ao comunicar com Gemini: {str(e)}"
