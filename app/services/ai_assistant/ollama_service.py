import re
from typing import Any

import httpx
from openai import APIConnectionError, AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_assistant.llm_base import LLMBaseService
from app.services.ai_assistant.tools import (
    execute_tool,
    get_openai_tools_schema,
    get_tools_summary,
)

SYSTEM_PROMPT_TEMPLATE = """Você é o assistente virtual do AssetTrack TI, um sistema ERP de gestão de ativos, chamados e manutenção de TI.

USUÁRIO ATUAL: {user_name} (Perfil: {user_role})

REGRAS DE OURO (Siga com rigor absoluto):
1. Chame o usuário pelo nome ({user_name}) em tom profissional e amigável.
2. NUNCA mencione os nomes das ferramentas (como [search_assets], [get_system_overview], etc.) em suas mensagens finais para o usuário. Elas são apenas para seu uso interno.
3. Se precisar de informações para responder (ativos, chamados, manutenções, etc.), ou se o usuário perguntar como usar o sistema / obter ajuda, você DEVE chamar a ferramenta correspondente usando o formato:
[CALL: nome_da_ferramenta {{"parametro": "valor"}}]
Não escreva nenhuma outra palavra ou introdução além do bloco [CALL].
4. Quando receber a resposta da ferramenta, use os dados reais fornecidos para responder de forma clara em português, sem citar que usou uma ferramenta.
5. Se não precisar de nenhuma ferramenta para responder (ex: saudações), responda normalmente de forma amigável.
6. PERFIL DE USUÁRIO COMUM (usuario_comum / rh): Para esses perfis, seja extremamente detalhado, paciente e explicativo. Forneça respostas completas e passo a passo sobre como realizar as operações (abrir chamados, solicitar manutenções, usar QR code). Sempre utilize a ferramenta `read_system_manual` para trazer as orientações exatas do manual do usuário e ajudá-lo a usar a aplicação com perfeição.

SUAS FERRAMENTAS INTERNAS (NUNCA REVELE ESTES NOMES AO USUÁRIO):
{tools_summary}

EXEMPLOS DE USO INTERNO:
- Pergunta: "quais ativos temos?" → Resposta: [CALL: search_assets {{}}]
- Pergunta: "me dá um resumo do sistema" → Resposta: [CALL: get_system_overview {{}}]
- Pergunta: "verifique o chamado 5" → Resposta: [CALL: search_all_tickets {{"query": "5"}}]
- Pergunta: "quais as categorias de ativos?" → Resposta: [CALL: list_categories {{}}]
- Pergunta: "como abro um chamado?" / "como funciona o módulo de compras?" → Resposta: [CALL: read_system_manual {{"document_name": "manual_do_usuario"}}]"""


class OllamaService(LLMBaseService):
    def __init__(self, api_key: str = "ollama", model: str = "gemma2:2b", base_url: str = "http://localhost:11434"):
        self.api_key = api_key if api_key else "ollama"
        self.model = model if model else "gemma2:2b"
        self.raw_base_url = base_url or "http://localhost:11434"
        self.client = self._build_client(self.raw_base_url)

    def _build_client(self, url: str) -> AsyncOpenAI:
        clean_base_url = url.rstrip("/")
        if not clean_base_url.endswith("/v1"):
            clean_base_url += "/v1"
        return AsyncOpenAI(api_key=self.api_key, base_url=clean_base_url)

    async def _try_completion(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None):
        # List of candidate URLs to auto-fallback if connection is refused
        candidates = [self.raw_base_url]
        for fallback in ["http://host.docker.internal:11434", "http://host.containers.internal:11434", "http://10.89.0.1:11434", "http://172.17.0.1:11434", "http://localhost:11434"]:
            if fallback not in candidates:
                candidates.append(fallback)

        last_conn_err = None
        for candidate_url in candidates:
            client = self._build_client(candidate_url)
            try:
                # Attempt with tools if provided
                if tools:
                    try:
                        resp = await client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            tools=tools,
                            tool_choice="auto"
                        )
                        self.client = client
                        return resp
                    except (APIConnectionError, httpx.ConnectError):
                        raise  # re-raise to hit the candidate loop
                    except Exception as schema_err:
                        print(f"[OllamaService] Tools call failed ({schema_err}). Retrying without tools on {candidate_url}...")
                        resp = await client.chat.completions.create(
                            model=self.model,
                            messages=messages
                        )
                        self.client = client
                        return resp
                else:
                    resp = await client.chat.completions.create(
                        model=self.model,
                        messages=messages
                    )
                    self.client = client
                    return resp
            except (APIConnectionError, httpx.ConnectError) as err:
                last_conn_err = err
                print(f"[OllamaService] Conexão falhou em '{candidate_url}'. Tentando próximo candidato...")
                continue

        # If all candidates failed:
        err_msg = (
            f"Não foi possível conectar ao servidor Ollama em '{self.raw_base_url}'. "
            "Certifique-se de que o serviço Ollama esteja rodando na máquina host e aceitando conexões de rede (variável OLLAMA_HOST=0.0.0.0 no host)."
        )
        print(f"[OllamaService] {err_msg} Detalhes: {last_conn_err}")
        raise RuntimeError(err_msg) from last_conn_err

    async def chat(
        self, db: AsyncSession, user_id: int, messages: list[dict[str, Any]], 
        allow_advanced_tools: bool = False, user_context: dict[str, str] | None = None
    ) -> str:
        user_name = user_context.get("nome", "Usuário") if user_context else "Usuário"
        user_role = user_context.get("role", "usuario_comum") if user_context else "usuario_comum"
        tools_summary = get_tools_summary(allow_advanced=allow_advanced_tools)
        
        system_content = SYSTEM_PROMPT_TEMPLATE.format(
            user_name=user_name, user_role=user_role, tools_summary=tools_summary
        )

        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_content})
        else:
            messages[0]["content"] = system_content

        tools = get_openai_tools_schema(allow_advanced=allow_advanced_tools)

        for iteration in range(5):
            response = await self._try_completion(messages, tools if tools else None)
            response_message = response.choices[0].message
            content = response_message.content or ""

            # 1. Native Tool Call checking
            if getattr(response_message, "tool_calls", None) and response_message.tool_calls:
                messages.append(response_message.model_dump(exclude_none=True))
                
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = tool_call.function.arguments
                    function_response = await execute_tool(db, user_id, function_name, function_args)
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": function_response,
                    })
                continue

            # 2. Text-based parsed Tool Call (ReAct format fallback)
            from app.services.ai_assistant.tools import (
                AVAILABLE_TOOLS,
                clean_unwanted_tool_tags,
            )
            matches = list(re.finditer(r'\[(?:CALL:\s*)?([a-zA-Z0-9_]+)(?:\s+({.*?}|\[.*?\])?)?\]', content))
            if matches:
                executed_any = False
                tool_results_text = []
                
                for match in matches:
                    tool_name = match.group(1)
                    tool_args_str = match.group(2) or "{}"
                    if not tool_args_str.startswith("{"):
                        tool_args_str = "{}"
                    if tool_name in AVAILABLE_TOOLS:
                        function_response = await execute_tool(db, user_id, tool_name, tool_args_str)
                        tool_results_text.append(f"Resultado da ferramenta {tool_name}:\n{function_response}")
                        executed_any = True
                
                if executed_any:
                    clean_assistant_content = clean_unwanted_tool_tags(content)
                    messages.append({"role": "assistant", "content": clean_assistant_content})
                    messages.append({
                        "role": "user",
                        "content": "\n\n".join(tool_results_text) + "\n\nUse esses dados reais fornecidos para responder ao usuário com os valores numéricos e detalhes em texto. NUNCA mencione nomes de ferramentas ou colchetes [ ]."
                    })
                    continue
                else:
                    clean_content = clean_unwanted_tool_tags(content)
                    return clean_content or "Desculpe, não consegui processar a solicitação."
            
            return clean_unwanted_tool_tags(content)
        
        return clean_unwanted_tool_tags(content)
