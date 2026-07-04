from app.services.ai_assistant.llm_base import LLMBaseService
from app.services.ai_assistant.openai_service import OpenAIService
from app.services.ai_assistant.gemini_service import GeminiService
from app.services.ai_assistant.groq_service import GroqService

def get_llm_service(provider: str, api_key: str, model_name: str = "") -> LLMBaseService:
    if not api_key:
        raise ValueError(f"API Key for provider {provider} is not configured.")
        
    if provider.lower() == "openai":
        # Default to gpt-4o-mini if not provided
        model = model_name if model_name else "gpt-4o-mini"
        return OpenAIService(api_key=api_key, model=model)
    elif provider.lower() == "gemini":
        # Default to gemini-2.5-flash if not provided
        model = model_name if model_name else "gemini-2.5-flash"
        return GeminiService(api_key=api_key, model=model)
    elif provider.lower() == "groq":
        # Default to llama-3.1-8b-instant if not provided
        model = model_name if model_name else "llama-3.1-8b-instant"
        return GroqService(api_key=api_key, model=model)
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
