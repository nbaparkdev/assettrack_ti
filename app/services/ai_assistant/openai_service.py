import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.services.ai_assistant.llm_base import LLMBaseService
from app.services.ai_assistant.tools import get_openai_tools_schema, execute_tool

class OpenAIService(LLMBaseService):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(self, db: AsyncSession, user_id: int, messages: List[Dict[str, Any]], allow_advanced_tools: bool = False) -> str:
        # Prepend system prompt if not present
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {
                "role": "system", 
                "content": "Você é o assistente virtual do AssetTrack TI. Você ajuda os usuários a gerenciar ativos, chamados e compras. Seja conciso e educado."
            })

        tools = get_openai_tools_schema(allow_advanced=allow_advanced_tools)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Handle tool calls
        if response_message.tool_calls:
            # We add the assistant message to the context
            messages.append(response_message.model_dump(exclude_none=True))
            
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = tool_call.function.arguments
                
                # Execute locally
                function_response = await execute_tool(db, user_id, function_name, function_args)
                
                # Add tool result to context
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response,
                })
                
            # Send context back to OpenAI to get the final language response
            final_response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return final_response.choices[0].message.content
        
        return response_message.content
