import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai

from app.services.ai_assistant.llm_base import LLMBaseService
from app.services.ai_assistant.tools import AVAILABLE_TOOLS, execute_tool, get_tools_summary

SYSTEM_PROMPT_TEMPLATE = """Você é o assistente virtual do AssetTrack TI, um sistema ERP de gestão de ativos, chamados e manutenção de TI.

USUÁRIO ATUAL: {user_name} (Perfil: {user_role})

REGRAS FUNDAMENTAIS:
1. Chame o usuário pelo nome ({user_name}) nas suas respostas para ser pessoal e acolhedor.
2. NUNCA invente ou alucine dados. TODOS os dados devem vir das suas ferramentas (functions).
3. Quando o usuário perguntar sobre QUALQUER dado do sistema (chamados, ativos, manutenções, equipamentos), você DEVE chamar a ferramenta apropriada ANTES de responder.
4. Se a ferramenta retornar "nenhum encontrado", informe isso de forma amigável.
5. Seja conciso, profissional e responda em português.

SUAS FERRAMENTAS DISPONÍVEIS:
{tools_summary}

INSTRUÇÕES DE USO OBRIGATÓRIO:
- "tem chamados?" / "quais os tickets?" → chame search_all_tickets ou get_my_active_tickets
- "lista os ativos" / "quais equipamentos?" → chame search_assets  
- "resumo do sistema" / "como está o sistema?" → chame get_system_overview
- "manutenções" / "ordens de serviço" → chame get_maintenance_report
- "ativos disponíveis" / "em manutenção" → chame get_assets_by_status
- "abre um chamado" / "quero reportar" → chame create_service_desk_ticket
- QUALQUER pergunta sobre dados do sistema → USE uma ferramenta. NUNCA responda sem dados reais."""


def _build_function_declarations(allow_advanced: bool = False):
    """Build Gemini FunctionDeclaration protos from tool registry."""
    declarations = []
    for name, metadata in AVAILABLE_TOOLS.items():
        if metadata.get("advanced", False) and not allow_advanced:
            continue
        declarations.append(
            genai.protos.FunctionDeclaration(
                name=name,
                description=metadata["description"]
            )
        )
    return declarations


class GeminiService(LLMBaseService):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        
    async def chat(
        self, db: AsyncSession, user_id: int, messages: List[Dict[str, Any]], 
        allow_advanced_tools: bool = False, user_context: Optional[Dict[str, str]] = None
    ) -> str:
        user_name = user_context.get("nome", "Usuário") if user_context else "Usuário"
        user_role = user_context.get("role", "usuario_comum") if user_context else "usuario_comum"
        tools_summary = get_tools_summary(allow_advanced=allow_advanced_tools)
        
        system_content = SYSTEM_PROMPT_TEMPLATE.format(
            user_name=user_name, user_role=user_role, tools_summary=tools_summary
        )
        
        # Build tool declarations
        declarations = _build_function_declarations(allow_advanced=allow_advanced_tools)
        tools_config = [genai.protos.Tool(function_declarations=declarations)] if declarations else None
        
        model = genai.GenerativeModel(
            self.model_name,
            system_instruction=system_content,
            tools=tools_config
        )

        # Convert OpenAI format messages to Gemini format
        history = []
        for msg in messages:
            if msg["role"] == "system":
                continue
            role = "user" if msg["role"] == "user" else "model"
            content = msg.get("content", "")
            if content:
                history.append({"role": role, "parts": [content]})
        
        if not history:
            return "Envie uma mensagem para começar."
        
        chat_session = model.start_chat(history=history[:-1])
        last_user_message = history[-1]["parts"][0]
        
        try:
            response = chat_session.send_message(last_user_message)
            
            # Check if Gemini wants to call a function
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call and part.function_call.name:
                        fn_name = part.function_call.name
                        fn_args = dict(part.function_call.args) if part.function_call.args else {}
                        
                        tool_result = await execute_tool(
                            db=db, user_id=user_id, 
                            tool_name=fn_name, arguments_json=json.dumps(fn_args)
                        )
                        
                        response2 = chat_session.send_message(
                            genai.protos.Content(
                                parts=[genai.protos.Part(
                                    function_response=genai.protos.FunctionResponse(
                                        name=fn_name,
                                        response={"result": tool_result}
                                    )
                                )]
                            )
                        )
                        return response2.text
            
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "ResourceExhausted" in error_str or "quota" in error_str.lower():
                return ("⚠️ **Limite de requisições do Gemini atingido.**\n\n"
                        "O plano gratuito da API Gemini tem um limite de 20 requisições por dia.\n\n"
                        "**Opções:**\n"
                        "- Troque o provedor para **Groq** ou **OpenAI** no painel Admin > Módulos.\n"
                        "- Aguarde alguns minutos e tente novamente.\n"
                        "- Faça upgrade do plano Gemini no Google AI Studio.")
            import traceback
            print(f"Gemini Error: {traceback.format_exc()}")
            return f"Erro ao comunicar com Gemini: {error_str}"
