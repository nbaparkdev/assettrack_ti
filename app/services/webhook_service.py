import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.webhook import Webhook, WebhookLog
import asyncio
from app.database import SessionLocal

from datetime import datetime

WEBHOOK_EVENTS = [
    "ASSET_CREATED",
    "ASSET_UPDATED",
    "ASSET_DELETED",
    "ASSET_REQUEST_CREATED",
    "ASSET_REQUEST_APPROVED",
    "ASSET_REQUEST_REJECTED",
    "ASSET_REQUEST_DELIVERED",
    "MAINTENANCE_REQUESTED",
    "MAINTENANCE_ACCEPTED",
    "MAINTENANCE_REJECTED",
    "MAINTENANCE_COMPLETED",
    "MAINTENANCE_DELIVERED",
    "PREVENTIVE_PLAN_CREATED",
    "PREVENTIVE_ORDER_CREATED",
    "PREVENTIVE_ORDER_STARTED",
    "PREVENTIVE_ORDER_COMPLETED",
    "PREVENTIVE_ORDER_CANCELLED",
    "TICKET_CREATED",
    "TICKET_UPDATED",
    "TICKET_ASSIGNED",
    "TICKET_RESOLVED",
    "TICKET_CANCELLED",
    "TICKET_INTERACTION_ADDED",
    "EMERGENCY_ALERT_TRIGGERED",
    "KANBAN_CARD_MOVED",
    "PURCHASE_REQUEST_CREATED",
    "PURCHASE_REQUEST_APPROVED",
    "PURCHASE_REQUEST_REJECTED",
    "PURCHASE_QUOTATION_CREATED",
    "PURCHASE_ORDER_CREATED",
    "PURCHASE_ORDER_RECEIVED"
]

WEBHOOK_EVENT_DETAILS = {
    # Gestão de Ativos
    "ASSET_CREATED": {
        "key": "ASSET_CREATED",
        "label": "Ativo Criado",
        "desc": "Disparado quando um novo patrimônio/ativo é cadastrado.",
        "categoria": "Gestão de Ativos"
    },
    "ASSET_UPDATED": {
        "key": "ASSET_UPDATED",
        "label": "Ativo Atualizado",
        "desc": "Disparado quando as informações de um ativo são alteradas.",
        "categoria": "Gestão de Ativos"
    },
    "ASSET_DELETED": {
        "key": "ASSET_DELETED",
        "label": "Ativo Excluído",
        "desc": "Disparado quando um ativo é removido do sistema.",
        "categoria": "Gestão de Ativos"
    },

    # Solicitações de Ativos
    "ASSET_REQUEST_CREATED": {
        "key": "ASSET_REQUEST_CREATED",
        "label": "Solicitação de Ativo Criada",
        "desc": "Quando um colaborador solicita a posse ou uso de um equipamento.",
        "categoria": "Solicitações de Ativos"
    },
    "ASSET_REQUEST_APPROVED": {
        "key": "ASSET_REQUEST_APPROVED",
        "label": "Solicitação de Ativo Aprovada",
        "desc": "Quando a solicitação de ativo é aprovada pelo gestor/admin.",
        "categoria": "Solicitações de Ativos"
    },
    "ASSET_REQUEST_REJECTED": {
        "key": "ASSET_REQUEST_REJECTED",
        "label": "Solicitação de Ativo Rejeitada",
        "desc": "Quando a solicitação de ativo é indeferida.",
        "categoria": "Solicitações de Ativos"
    },
    "ASSET_REQUEST_DELIVERED": {
        "key": "ASSET_REQUEST_DELIVERED",
        "label": "Entrega de Ativo Confirmada",
        "desc": "Quando a entrega física do equipamento é confirmada ao usuário.",
        "categoria": "Solicitações de Ativos"
    },

    # Service Desk / Chamados
    "TICKET_CREATED": {
        "key": "TICKET_CREATED",
        "label": "Chamado de Suporte Criado",
        "desc": "Quando um novo ticket de Service Desk é aberto.",
        "categoria": "Service Desk (Chamados)"
    },
    "TICKET_UPDATED": {
        "key": "TICKET_UPDATED",
        "label": "Chamado Atualizado",
        "desc": "Quando informações ou prioridade do chamado são alteradas.",
        "categoria": "Service Desk (Chamados)"
    },
    "TICKET_ASSIGNED": {
        "key": "TICKET_ASSIGNED",
        "label": "Técnico Atribuído ao Chamado",
        "desc": "Quando um técnico de TI assume a responsabilidade do chamado.",
        "categoria": "Service Desk (Chamados)"
    },
    "TICKET_RESOLVED": {
        "key": "TICKET_RESOLVED",
        "label": "Chamado Resolvido",
        "desc": "Quando a solução do chamado é concluída pelo suporte.",
        "categoria": "Service Desk (Chamados)"
    },
    "TICKET_CANCELLED": {
        "key": "TICKET_CANCELLED",
        "label": "Chamado Cancelado",
        "desc": "Quando um chamado é cancelado antes da resolução.",
        "categoria": "Service Desk (Chamados)"
    },
    "TICKET_INTERACTION_ADDED": {
        "key": "TICKET_INTERACTION_ADDED",
        "label": "Comentário / Interação Registrada",
        "desc": "Nova resposta ou atualização enviada no histórico do chamado.",
        "categoria": "Service Desk (Chamados)"
    },

    # Manutenção Corretiva
    "MAINTENANCE_REQUESTED": {
        "key": "MAINTENANCE_REQUESTED",
        "label": "Manutenção Corretiva Solicitada",
        "desc": "Abertura de pedido de reparo para equipamento com defeito.",
        "categoria": "Manutenção Corretiva"
    },
    "MAINTENANCE_ACCEPTED": {
        "key": "MAINTENANCE_ACCEPTED",
        "label": "Manutenção Corretiva Aceita",
        "desc": "Quando o técnico aceita o pedido de manutenção.",
        "categoria": "Manutenção Corretiva"
    },
    "MAINTENANCE_REJECTED": {
        "key": "MAINTENANCE_REJECTED",
        "label": "Manutenção Corretiva Rejeitada",
        "desc": "Quando a solicitação de reparo é recusada.",
        "categoria": "Manutenção Corretiva"
    },
    "MAINTENANCE_COMPLETED": {
        "key": "MAINTENANCE_COMPLETED",
        "label": "Manutenção Corretiva Concluída",
        "desc": "Quando o conserto do equipamento é concluído com sucesso.",
        "categoria": "Manutenção Corretiva"
    },
    "MAINTENANCE_DELIVERED": {
        "key": "MAINTENANCE_DELIVERED",
        "label": "Equipamento Entregue pós-Manutenção",
        "desc": "Quando o equipamento reparado é devolvido ao usuário.",
        "categoria": "Manutenção Corretiva"
    },

    # Manutenção Preventiva
    "PREVENTIVE_PLAN_CREATED": {
        "key": "PREVENTIVE_PLAN_CREATED",
        "label": "Plano Preventivo Criado",
        "desc": "Cadastro de novo plano recorrente de revisão periódica.",
        "categoria": "Manutenção Preventiva"
    },
    "PREVENTIVE_ORDER_CREATED": {
        "key": "PREVENTIVE_ORDER_CREATED",
        "label": "Ordem Preventiva Gerada",
        "desc": "Emissão de Ordem de Serviço (OS) preventiva de rotina.",
        "categoria": "Manutenção Preventiva"
    },
    "PREVENTIVE_ORDER_STARTED": {
        "key": "PREVENTIVE_ORDER_STARTED",
        "label": "Ordem Preventiva Iniciada",
        "desc": "Início do atendimento técnico na OS preventiva.",
        "categoria": "Manutenção Preventiva"
    },
    "PREVENTIVE_ORDER_COMPLETED": {
        "key": "PREVENTIVE_ORDER_COMPLETED",
        "label": "Ordem Preventiva Concluída",
        "desc": "Finalização com sucesso da revisão preventiva.",
        "categoria": "Manutenção Preventiva"
    },
    "PREVENTIVE_ORDER_CANCELLED": {
        "key": "PREVENTIVE_ORDER_CANCELLED",
        "label": "Ordem Preventiva Cancelada",
        "desc": "Cancelamento da Ordem de Serviço preventiva.",
        "categoria": "Manutenção Preventiva"
    },

    # Gestão de Compras (Procurement)
    "PURCHASE_REQUEST_CREATED": {
        "key": "PURCHASE_REQUEST_CREATED",
        "label": "Solicitação de Compra Criada",
        "desc": "Abertura de nova requisição de compras pelo setor.",
        "categoria": "Gestão de Compras (Procurement)"
    },
    "PURCHASE_REQUEST_APPROVED": {
        "key": "PURCHASE_REQUEST_APPROVED",
        "label": "Solicitação de Compra Aprovada",
        "desc": "Aprovação final da requisição de compra pelos gestores.",
        "categoria": "Gestão de Compras (Procurement)"
    },
    "PURCHASE_REQUEST_REJECTED": {
        "key": "PURCHASE_REQUEST_REJECTED",
        "label": "Solicitação de Compra Reprovada",
        "desc": "Indeferimento da requisição de compra.",
        "categoria": "Gestão de Compras (Procurement)"
    },
    "PURCHASE_QUOTATION_CREATED": {
        "key": "PURCHASE_QUOTATION_CREATED",
        "label": "Cotação de Preços Registrada",
        "desc": "Início da pesquisa de preços com fornecedores.",
        "categoria": "Gestão de Compras (Procurement)"
    },
    "PURCHASE_ORDER_CREATED": {
        "key": "PURCHASE_ORDER_CREATED",
        "label": "Pedido de Compra Emitido",
        "desc": "Geração do Pedido de Compra (PO) para o fornecedor vencedor.",
        "categoria": "Gestão de Compras (Procurement)"
    },
    "PURCHASE_ORDER_RECEIVED": {
        "key": "PURCHASE_ORDER_RECEIVED",
        "label": "Recebimento de Pedido Confirmado",
        "desc": "Entrada de produtos ou confirmação de nota fiscal no sistema.",
        "categoria": "Gestão de Compras (Procurement)"
    },

    # Alertas & Outros
    "EMERGENCY_ALERT_TRIGGERED": {
        "key": "EMERGENCY_ALERT_TRIGGERED",
        "label": "Alerta de Emergência Disparado",
        "desc": "Acionamento do botão de emergência/pânico pelo usuário.",
        "categoria": "Alertas e Projetos"
    },
    "KANBAN_CARD_MOVED": {
        "key": "KANBAN_CARD_MOVED",
        "label": "Card Kanban Movimentado",
        "desc": "Movimentação de cartão de projeto entre colunas do Kanban.",
        "categoria": "Alertas e Projetos"
    },
}

def get_grouped_webhook_events() -> dict:
    """
    Returns events grouped by category for template rendering.
    """
    groups = {}
    for key, info in WEBHOOK_EVENT_DETAILS.items():
        cat = info["categoria"]
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(info)
    return groups

async def dispatch_webhook_event(evento: str, payload: dict):
    """
    Sends a POST request to all active webhooks subscribed to the given event.
    Logs the attempt and outcome. This should run in a background task.
    """
    try:
        if evento not in WEBHOOK_EVENTS:
            return
            
        async with SessionLocal() as db:
            result = await db.execute(select(Webhook).filter(Webhook.is_active == True))
            webhooks = result.scalars().all()
            
            target_webhooks = []
            for w in webhooks:
                try:
                    eventos_permitidos = json.loads(w.eventos_permitidos)
                    if evento in eventos_permitidos:
                        target_webhooks.append(w)
                except:
                    pass
                    
            if not target_webhooks:
                return

            payload_str = json.dumps(payload)
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                async def _send_single_webhook(w):
                    log_entry = WebhookLog(
                        webhook_id=w.id,
                        evento=evento,
                        payload_enviado=payload_str,
                        sucesso=False
                    )
                    db.add(log_entry)
                    try:
                        response = await client.post(w.url, json=payload)
                        log_entry.status_code = response.status_code
                        log_entry.response_body = response.text[:2000] # Limit to 2000 chars
                        if 200 <= response.status_code < 300:
                            log_entry.sucesso = True
                    except Exception as e:
                        log_entry.response_body = str(e)[:2000]
                        log_entry.status_code = 0

                await asyncio.gather(*[_send_single_webhook(w) for w in target_webhooks], return_exceptions=True)
                await db.commit()
    except Exception as e:
        print(f"[WEBHOOK][ERRO] Falha ao despachar evento {evento}: {e}")


async def send_test_webhook_event(webhook_id: int) -> tuple[bool, str]:
    """
    Sends a TEST event payload to a specific webhook ID.
    Returns (success: bool, message: str)
    """
    async with SessionLocal() as db:
        result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
        webhook = result.scalars().first()
        if not webhook:
            return False, "Webhook não encontrado"

        test_payload = {
            "event": "TEST_WEBHOOK",
            "message": "Este é um disparo de teste enviado pelo AssetTrack TI.",
            "timestamp": datetime.now().isoformat(),
            "webhook_id": webhook.id,
            "webhook_nome": webhook.nome,
            "detalhes": {
                "solicitacao_id": 9999,
                "os_numero": "OS-TESTE-2026",
                "patrimonio": "PAT-9999",
                "asset_nome": "Servidor Teste Webhook",
                "tecnico_responsavel": "Técnico Teste",
                "solicitante": "Administrador",
                "status": "TESTE",
                "datas": {
                    "abertura": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "observacoes": "Disparo de verificação de integração com o webhook."
            }
        }

        payload_str = json.dumps(test_payload)
        log_entry = WebhookLog(
            webhook_id=webhook.id,
            evento="TEST_WEBHOOK",
            payload_enviado=payload_str,
            sucesso=False
        )
        db.add(log_entry)

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.post(webhook.url, json=test_payload)
                log_entry.status_code = response.status_code
                log_entry.response_body = response.text[:2000]
                if 200 <= response.status_code < 300:
                    log_entry.sucesso = True
                    await db.commit()
                    return True, f"Teste enviado com sucesso! Status HTTP: {response.status_code}"
                else:
                    await db.commit()
                    return False, f"Servidor de destino respondeu com erro HTTP {response.status_code}."
        except Exception as e:
            log_entry.status_code = 0
            log_entry.response_body = str(e)[:2000]
            await db.commit()
            return False, f"Falha ao conectar na URL: {str(e)}"


def format_maintenance_request_payload(solicitacao, evento: str) -> dict:
    """
    Format payload for Corrective Maintenance Request events.
    """
    status_val = solicitacao.status.value if hasattr(solicitacao.status, 'value') else str(solicitacao.status)
    prioridade_val = solicitacao.prioridade.value if hasattr(solicitacao.prioridade, 'value') else str(solicitacao.prioridade)
    
    asset_nome = solicitacao.asset.nome if getattr(solicitacao, 'asset', None) else None
    patrimonio = solicitacao.asset.e_patrimonio if getattr(solicitacao, 'asset', None) else None

    solicitante_nome = solicitacao.solicitante.nome if getattr(solicitacao, 'solicitante', None) else None
    solicitante_email = solicitacao.solicitante.email if getattr(solicitacao, 'solicitante', None) else None

    tecnico_nome = solicitacao.responsavel.nome if getattr(solicitacao, 'responsavel', None) else None
    tecnico_email = solicitacao.responsavel.email if getattr(solicitacao, 'responsavel', None) else None

    return {
        "event": evento,
        "solicitacao_id": solicitacao.id,
        "tipo_manutencao": "CORRETIVA",
        "status": status_val,
        "prioridade": prioridade_val,
        "descricao": solicitacao.descricao,
        "observacao": getattr(solicitacao, 'observacao_resposta', None),
        "observacao_conclusao": getattr(solicitacao, 'observacao_conclusao', None),
        "ativo": {
            "id": solicitacao.asset_id,
            "nome": asset_nome,
            "patrimonio": patrimonio,
        },
        "solicitante": {
            "id": solicitacao.solicitante_id,
            "nome": solicitante_nome,
            "email": solicitante_email,
        },
        "tecnico_responsavel": {
            "id": solicitacao.responsavel_id,
            "nome": tecnico_nome,
            "email": tecnico_email,
        } if solicitacao.responsavel_id else None,
        "datas": {
            "solicitacao": solicitacao.data_solicitacao.strftime("%Y-%m-%d %H:%M:%S") if getattr(solicitacao, 'data_solicitacao', None) else None,
            "conclusao": solicitacao.data_conclusao.strftime("%Y-%m-%d %H:%M:%S") if getattr(solicitacao, 'data_conclusao', None) else None,
        }
    }


def format_preventive_order_payload(order, evento: str) -> dict:
    """
    Format payload for Preventive Maintenance Order events.
    """
    status_val = order.status.value if hasattr(order.status, 'value') else str(order.status)
    prioridade_val = order.prioridade.value if hasattr(order.prioridade, 'value') else str(order.prioridade)
    tipo_val = order.tipo.value if hasattr(order.tipo, 'value') else str(order.tipo)

    asset_nome = order.asset.nome if getattr(order, 'asset', None) else (order.infra_predial_servico or "N/A")
    patrimonio = order.asset.e_patrimonio if getattr(order, 'asset', None) else None

    tecnico_nome = order.tecnico.nome if getattr(order, 'tecnico', None) else None
    tecnico_email = order.tecnico.email if getattr(order, 'tecnico', None) else None

    return {
        "event": evento,
        "os_id": order.id,
        "os_numero": order.numero,
        "tipo_manutencao": "PREVENTIVA",
        "tipo_servico": tipo_val,
        "status": status_val,
        "prioridade": prioridade_val,
        "descricao_observacoes": order.observacoes,
        "custo_total": float(order.custo_total) if getattr(order, 'custo_total', None) is not None else 0.0,
        "tempo_total_minutos": order.tempo_total_minutos,
        "ativo": {
            "id": order.asset_id,
            "nome": asset_nome,
            "patrimonio": patrimonio,
        },
        "tecnico_responsavel": {
            "id": order.tecnico_id,
            "nome": tecnico_nome,
            "email": tecnico_email,
        } if order.tecnico_id else None,
        "datas": {
            "abertura": order.data_abertura.strftime("%Y-%m-%d %H:%M:%S") if getattr(order, 'data_abertura', None) else None,
            "agendada": order.data_agendada.strftime("%Y-%m-%d %H:%M:%S") if getattr(order, 'data_agendada', None) else None,
            "inicio": order.data_inicio.strftime("%Y-%m-%d %H:%M:%S") if getattr(order, 'data_inicio', None) else None,
            "conclusao": order.data_conclusao.strftime("%Y-%m-%d %H:%M:%S") if getattr(order, 'data_conclusao', None) else None,
        }
    }


def format_preventive_plan_payload(plan, evento: str) -> dict:
    """
    Format payload for Preventive Maintenance Plan events.
    """
    tipo_val = plan.tipo.value if hasattr(plan.tipo, 'value') else str(plan.tipo)
    periodicidade_val = plan.periodicidade.value if hasattr(plan.periodicidade, 'value') else str(plan.periodicidade)
    criticidade_val = plan.criticidade.value if hasattr(plan.criticidade, 'value') else str(plan.criticidade)

    return {
        "event": evento,
        "plano_id": plan.id,
        "codigo": plan.codigo,
        "nome": plan.nome,
        "tipo": tipo_val,
        "periodicidade": periodicidade_val,
        "criticidade": criticidade_val,
        "ativo": plan.ativo,
        "descricao": plan.descricao,
        "proxima_execucao": plan.proxima_execucao.strftime("%Y-%m-%d %H:%M:%S") if getattr(plan, 'proxima_execucao', None) else None,
    }


def format_service_ticket_payload(ticket, evento: str, interaction=None) -> dict:
    """
    Format payload for Service Desk ticket events.
    """
    status_val = ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status)
    prioridade_val = ticket.prioridade.value if hasattr(ticket.prioridade, 'value') else str(ticket.prioridade)

    servico_nome = ticket.servico.nome if getattr(ticket, 'servico', None) else None
    categoria_nome = ticket.servico.categoria.nome if getattr(ticket, 'servico', None) and getattr(ticket.servico, 'categoria', None) else None

    solicitante_nome = ticket.solicitante.nome if getattr(ticket, 'solicitante', None) else None
    solicitante_email = ticket.solicitante.email if getattr(ticket, 'solicitante', None) else None

    tecnico_nome = ticket.tecnico.nome if getattr(ticket, 'tecnico', None) else None
    tecnico_email = ticket.tecnico.email if getattr(ticket, 'tecnico', None) else None

    payload = {
        "event": evento,
        "ticket_id": ticket.id,
        "codigo": ticket.codigo,
        "titulo": ticket.titulo,
        "status": status_val,
        "prioridade": prioridade_val,
        "servico": {
            "id": ticket.servico_id,
            "nome": servico_nome,
            "categoria": categoria_nome,
        },
        "descricao": ticket.descricao,
        "solucao": ticket.solucao,
        "solicitante": {
            "id": ticket.solicitante_id,
            "nome": solicitante_nome,
            "email": solicitante_email,
        },
        "tecnico_responsavel": {
            "id": ticket.tecnico_id,
            "nome": tecnico_nome,
            "email": tecnico_email,
        } if ticket.tecnico_id else None,
        "datas": {
            "abertura": ticket.data_abertura.strftime("%Y-%m-%d %H:%M:%S") if getattr(ticket, 'data_abertura', None) else None,
            "atualizacao": ticket.data_atualizacao.strftime("%Y-%m-%d %H:%M:%S") if getattr(ticket, 'data_atualizacao', None) else None,
            "fechamento": ticket.data_fechamento.strftime("%Y-%m-%d %H:%M:%S") if getattr(ticket, 'data_fechamento', None) else None,
        }
    }

    if interaction:
        usuario_interacao = getattr(interaction.usuario, 'nome', None) if getattr(interaction, 'usuario', None) else None
        payload["interacao"] = {
            "id": getattr(interaction, 'id', None),
            "tipo": getattr(interaction, 'tipo', 'Comentário'),
            "mensagem": getattr(interaction, 'mensagem', None),
            "usuario": usuario_interacao
        }

    return payload


def format_asset_request_payload(solicitacao, evento: str) -> dict:
    """
    Format payload for Asset Request (Minhas Solicitações) events.
    """
    status_val = solicitacao.status.value if hasattr(solicitacao.status, 'value') else str(solicitacao.status)

    asset_nome = solicitacao.asset.nome if getattr(solicitacao, 'asset', None) else None
    patrimonio = solicitacao.asset.e_patrimonio if getattr(solicitacao, 'asset', None) else None

    solicitante_nome = solicitacao.solicitante.nome if getattr(solicitacao, 'solicitante', None) else None
    solicitante_email = solicitacao.solicitante.email if getattr(solicitacao, 'solicitante', None) else None

    aprovador_nome = solicitacao.aprovador.nome if getattr(solicitacao, 'aprovador', None) else None
    aprovador_email = solicitacao.aprovador.email if getattr(solicitacao, 'aprovador', None) else None

    confirmador_nome = solicitacao.confirmador.nome if getattr(solicitacao, 'confirmador', None) else None

    return {
        "event": evento,
        "solicitacao_id": solicitacao.id,
        "status": status_val,
        "motivo": solicitacao.motivo,
        "ativo": {
            "id": solicitacao.asset_id,
            "nome": asset_nome,
            "patrimonio": patrimonio,
        },
        "solicitante": {
            "id": solicitacao.solicitante_id,
            "nome": solicitante_nome,
            "email": solicitante_email,
        },
        "aprovador": {
            "id": solicitacao.aprovador_id,
            "nome": aprovador_nome,
            "email": aprovador_email,
        } if solicitacao.aprovador_id else None,
        "entrega": {
            "confirmado_por": confirmador_nome,
            "via_qr": bool(solicitacao.confirmado_via_qr),
            "observacao": solicitacao.observacao_entrega,
        } if solicitacao.data_entrega else None,
        "datas": {
            "solicitacao": solicitacao.data_solicitacao.strftime("%Y-%m-%d %H:%M:%S") if getattr(solicitacao, 'data_solicitacao', None) else None,
            "aprovacao": solicitacao.data_aprovacao.strftime("%Y-%m-%d %H:%M:%S") if getattr(solicitacao, 'data_aprovacao', None) else None,
            "prevista_devolucao": solicitacao.data_prevista_devolucao.strftime("%Y-%m-%d %H:%M:%S") if getattr(solicitacao, 'data_prevista_devolucao', None) else None,
            "entrega": solicitacao.data_entrega.strftime("%Y-%m-%d %H:%M:%S") if getattr(solicitacao, 'data_entrega', None) else None,
        }
    }


def format_purchase_request_payload(req, evento: str) -> dict:
    """
    Format payload for Purchase Request (Solicitação de Compra) events.
    """
    status_val = req.status.value if hasattr(req.status, 'value') else str(req.status)
    solicitante_nome = req.solicitante.nome if getattr(req, 'solicitante', None) else None
    solicitante_email = req.solicitante.email if getattr(req, 'solicitante', None) else None
    centro_custo = req.centro_custo.nome if getattr(req, 'centro_custo', None) else None

    itens_list = []
    if getattr(req, 'itens', None):
        for item in req.itens:
            prod_nome = item.product.nome if getattr(item, 'product', None) else None
            forn_nome = item.fornecedor_sugerido.nome if getattr(item, 'fornecedor_sugerido', None) else None
            itens_list.append({
                "produto_id": item.product_id,
                "produto_nome": prod_nome,
                "quantidade": float(item.quantidade),
                "valor_estimado": float(item.valor_estimado),
                "fornecedor_sugerido": forn_nome,
            })

    total_estimado = sum(float(item.quantidade) * float(item.valor_estimado) for item in getattr(req, 'itens', []))

    return {
        "event": evento,
        "solicitacao_id": req.id,
        "numero": req.numero,
        "status": status_val,
        "urgencia": req.urgencia,
        "justificativa": req.justificativa,
        "centro_custo": centro_custo,
        "total_estimado": total_estimado,
        "solicitante": {
            "id": req.solicitante_id,
            "nome": solicitante_nome,
            "email": solicitante_email,
        },
        "itens": itens_list,
        "datas": {
            "criacao": req.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if getattr(req, 'data_criacao', None) else None,
            "necessaria": req.data_necessaria.strftime("%Y-%m-%d %H:%M:%S") if getattr(req, 'data_necessaria', None) else None,
        }
    }


def format_purchase_order_payload(order, evento: str) -> dict:
    """
    Format payload for Purchase Order (Pedido de Compra) events.
    """
    status_val = order.status.value if hasattr(order.status, 'value') else str(order.status)
    fornecedor_nome = order.fornecedor.nome if getattr(order, 'fornecedor', None) else None
    centro_custo = order.centro_custo.nome if getattr(order, 'centro_custo', None) else None

    itens_list = []
    if getattr(order, 'itens', None):
        for item in order.itens:
            prod_nome = item.product.nome if getattr(item, 'product', None) else None
            itens_list.append({
                "produto_id": item.product_id,
                "produto_nome": prod_nome,
                "quantidade": float(item.quantidade),
                "valor_unitario": float(item.valor_unitario),
                "total_item": float(item.total_item),
            })

    return {
        "event": evento,
        "pedido_id": order.id,
        "numero": order.numero,
        "status": status_val,
        "fornecedor": {
            "id": order.fornecedor_id,
            "nome": fornecedor_nome,
        },
        "centro_custo": centro_custo,
        "valor_total": float(order.valor_total),
        "frete": float(order.frete),
        "itens": itens_list,
        "data_emissao": order.data_emissao.strftime("%Y-%m-%d %H:%M:%S") if getattr(order, 'data_emissao', None) else None,
    }


def format_purchase_quotation_payload(cq, evento: str) -> dict:
    """
    Format payload for Purchase Quotation (Cotação de Compra) events.
    """
    solicitacao_num = cq.request.numero if getattr(cq, 'request', None) else None

    fornecedores_list = []
    if getattr(cq, 'suppliers', None):
        for supplier in cq.suppliers:
            forn_nome = supplier.fornecedor.nome if getattr(supplier, 'fornecedor', None) else None
            fornecedores_list.append({
                "fornecedor_id": supplier.fornecedor_id,
                "fornecedor_nome": forn_nome,
                "valor_total": float(supplier.valor_total),
                "prazo_entrega_dias": supplier.prazo_entrega_dias,
                "escolhido": bool(supplier.escolhido),
            })

    return {
        "event": evento,
        "cotacao_id": cq.id,
        "numero": cq.numero,
        "status": cq.status,
        "solicitacao_numero": solicitacao_num,
        "fornecedores": fornecedores_list,
        "data_criacao": cq.data_criacao.strftime("%Y-%m-%d %H:%M:%S") if getattr(cq, 'data_criacao', None) else None,
    }





