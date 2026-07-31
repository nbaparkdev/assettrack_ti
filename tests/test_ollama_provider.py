import pytest
from app.services.ai_assistant.llm_factory import get_llm_service
from app.services.ai_assistant.ollama_service import OllamaService

def test_ollama_factory():
    service = get_llm_service(
        provider="ollama",
        api_key="",
        model_name="gemma2:2b",
        base_url="http://localhost:11434"
    )
    assert isinstance(service, OllamaService)
    assert service.model == "gemma2:2b"
    assert str(service.client.base_url) == "http://localhost:11434/v1/"
