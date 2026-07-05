# app/services/ai_assistant/groq_service.py
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from groq import AsyncGroq
from app.services.ai_assistant.llm_base import LLMBaseService
from app.services.ai_assistant.tools import execute_tool, get_openai_tools_schema, get_tools_summary

SYSTEM_PROMPT_TEMPLATE = """Você é o assistente virtual do AssetTrack TI, um sistema ERP de gestão de ativos, chamados e manutenção de TI.

USUÁRIO ATUAL: {user_name} (Perfil: {user_role})

REGRAS FUNDAMENTAIS:
1. Chame o usuário pelo nome ({user_name}) nas suas respostas para ser pessoal e acolhedor.
2. NUNCA invente ou alucine dados. TODOS os dados devem vir das suas ferramentas (functions).
3. Quando o usuário perguntar sobre QUALQUER dado do sistema (chamados, ativos, manutenções, equipamentos), você DEVE chamar a ferramenta apropriada ANTES de responder.
4. Se a ferramenta retornar "nenhum encontrado", informe isso de forma amigável.
5. Seja conciso, profissional e responda em português.
6. Formate suas respostas com **negrito** para destaques e use listas para dados.

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


class GroqService(LLMBaseService):
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

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

        system_prompt = {"role": "system", "content": system_content}
        
        if not messages or messages[0].get("role") != "system":
            formatted_messages = [system_prompt] + messages
        else:
            messages[0]["content"] = system_content
            formatted_messages = messages

        tools = get_openai_tools_schema(allow_advanced=allow_advanced_tools)
        import groq
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
        except groq.BadRequestError as e:
            error_str = str(e)
            if "model_decommissioned" in error_str or "no longer supported" in error_str:
                # Dynamically fetch available models from Groq to guarantee we pick a live one
                print(f"Groq Model {self.model} decommissioned. Querying available models...")
                try:
                    available_models = await self.client.models.list()
                    fallback_model = None
                    
                    if available_models and hasattr(available_models, 'data') and available_models.data:
                        # Prefer a known good architecture if available, otherwise just grab the first one
                        fallback_model = available_models.data[-1].id
                        for m in available_models.data:
                            if any(x in m.id for x in ["groq", "llama-3.1", "qwen", "llama", "mixtral", "gpt-oss"]):
                                fallback_model = m.id
                                break
                    
                    if fallback_model:
                        print(f"Falling back to dynamically found model: {fallback_model}")
                        self.model = fallback_model
                        response = await self.client.chat.completions.create(
                            model=self.model,
                            messages=formatted_messages,
                            tools=tools if tools else None,
                            tool_choice="auto" if tools else None
                        )
                    else:
                        raise ValueError("No available models found from Groq API.")
                except Exception as ex:
                    print(f"Failed to dynamically fetch or use fallback model: {ex}")
                    raise e
            else:
                raise e

        response_message = response.choices[0].message

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                
                function_response = await execute_tool(
                    db=db, user_id=user_id, 
                    tool_name=function_name, arguments_json=function_args
                )
                
                formatted_messages.append({
                    "role": "assistant",
                    "tool_calls": [{
                        "id": tool_call.id, "type": "function",
                        "function": {"name": function_name, "arguments": tool_call.function.arguments}
                    }]
                })
                formatted_messages.append({
                    "role": "tool", "tool_call_id": tool_call.id,
                    "name": function_name, "content": function_response
                })

            second_response = await self.client.chat.completions.create(
                model=self.model, messages=formatted_messages
            )
            return second_response.choices[0].message.content or "Nenhuma resposta fornecida."

        return response_message.content or "Nenhuma resposta fornecida."
