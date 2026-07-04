import json
from typing import List, Dict, Any, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.transaction import Solicitacao, StatusSolicitacao
from app.models.asset import Asset
from app.models.user import User
from datetime import datetime
from sqlalchemy import or_, and_

async def get_my_active_tickets(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna um resumo das solicitações/tickets ativos do usuário."""
    stmt = select(Solicitacao).where(
        Solicitacao.solicitante_id == user_id,
        Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA])
    )
    result = await db.execute(stmt)
    solicitacoes = result.scalars().all()
    
    if not solicitacoes:
        return "Nenhuma solicitação ativa encontrada no momento."
    
    resumo = "Suas solicitações ativas:\n"
    for s in solicitacoes:
        resumo += f"- Ticket #{s.id}: Status {s.status.value}\n"
    return resumo

async def search_assets(db: AsyncSession, user_id: int, query: str = "", **kwargs) -> str:
    """Busca ativos no sistema por nome, tag ou status."""
    stmt = select(Asset)
    if query:
        stmt = stmt.where(or_(
            Asset.name.ilike(f"%{query}%"),
            Asset.asset_tag.ilike(f"%{query}%")
        ))
    result = await db.execute(stmt)
    assets = result.scalars().all()
    
    if not assets:
        return "Nenhum ativo encontrado com esse termo."
        
    resumo = "Ativos encontrados:\n"
    for a in assets[:10]: # limite de 10
        status_a = getattr(a, 'status', 'Desconhecido')
        resumo += f"- {a.name} (Tag: {a.asset_tag}) - Status: {status_a}\n"
    return resumo

async def create_service_desk_ticket(db: AsyncSession, user_id: int, title: str, description: str, **kwargs) -> str:
    """Cria um novo chamado de TI para o usuário."""
    nova_solicitacao = Solicitacao(
        solicitante_id=user_id,
        status=StatusSolicitacao.PENDENTE,
        data_solicitacao=datetime.now(),
        # Aqui seriam preenchidos os dados reais. No sistema atual precisaria da categoria e prioridade.
        # Por simplificação, vamos assumir que apenas o título e descrição são colocados em uma nota interna.
        observacoes=f"TÍTULO: {title}\nDESC: {description}\n\nCriado via Assistente IA."
    )
    db.add(nova_solicitacao)
    await db.commit()
    await db.refresh(nova_solicitacao)
    return f"Chamado #{nova_solicitacao.id} criado com sucesso! Em breve a TI analisará."

AVAILABLE_TOOLS = {
    "get_my_active_tickets": {
        "description": "Busca todas as solicitações e tickets ativos/pendentes do usuário atual.",
        "func": get_my_active_tickets,
        "advanced": False,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "search_assets": {
        "description": "Busca ativos, computadores ou patrimônios no sistema através de um termo.",
        "func": search_assets,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "O termo para buscar (ex: notebook, impressora, NB-001)."
                }
            },
            "required": ["query"]
        }
    },
    "create_service_desk_ticket": {
        "description": "Abre/cria um novo chamado ou ticket de suporte de TI para o usuário.",
        "func": create_service_desk_ticket,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Título ou resumo breve do problema."
                },
                "description": {
                    "type": "string",
                    "description": "Descrição detalhada do problema relatado pelo usuário."
                }
            },
            "required": ["title", "description"]
        }
    }
}

def get_openai_tools_schema(allow_advanced: bool = False) -> List[Dict[str, Any]]:
    tools = []
    for name, metadata in AVAILABLE_TOOLS.items():
        if metadata.get("advanced", False) and not allow_advanced:
            continue
            
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": metadata["description"],
                "parameters": metadata["parameters"]
            }
        })
    return tools

async def execute_tool(db: AsyncSession, user_id: int, tool_name: str, arguments_json: str) -> str:
    if tool_name not in AVAILABLE_TOOLS:
        return f"Error: Function {tool_name} not found."
    
    try:
        kwargs = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError:
        kwargs = {}
        
    func = AVAILABLE_TOOLS[tool_name]["func"]
    try:
        result = await func(db=db, user_id=user_id, **kwargs)
        return str(result)
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"
