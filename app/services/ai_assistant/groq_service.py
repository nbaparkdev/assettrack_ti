# app/services/ai_assistant/groq_service.py
import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from groq import AsyncGroq
from app.services.ai_assistant.llm_base import LLMBaseService
from app.services.ai_assistant.tools import execute_tool, get_openai_tools_schema

class GroqService(LLMBaseService):
    def __init__(self, api_key: str, model: str = "llama-3.1-8b-instant"):
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def chat(self, db: AsyncSession, user_id: int, messages: List[Dict[str, Any]], allow_advanced_tools: bool = False) -> str:
        # Define system prompt
        system_prompt = {
            "role": "system", 
            "content": "Você é o assistente virtual do AssetTrack TI. Ajude os usuários a gerenciar ativos e chamados de forma concisa. Responda em Markdown."
        }
        
        # Ensure system prompt is the first message
        if not messages or messages[0].get("role") != "system":
            formatted_messages = [system_prompt] + messages
        else:
            formatted_messages = messages

        # Get the schema (Groq uses the same JSON schema format as OpenAI for function calling)
        tools = get_openai_tools_schema(allow_advanced=allow_advanced_tools)

        # Call Groq API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        # Check if the model decided to call a function
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Execute the actual function
                function_response = await execute_tool(
                    db=db, 
                    user_id=user_id, 
                    function_name=function_name, 
                    arguments=function_args
                )
                
                # Append tool call and result to history
                formatted_messages.append({
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": function_name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": json.dumps(function_response)
                })

            # Send back to Groq with the function results
            second_response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages
            )
            return second_response.choices[0].message.content or "Nenhuma resposta fornecida após processar a ação."

        return response_message.content or "Nenhuma resposta fornecida."
