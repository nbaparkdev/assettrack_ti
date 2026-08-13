import pytest
import json
from app.services.webhook_service import (
    WEBHOOK_EVENTS,
    format_maintenance_request_payload,
    format_preventive_order_payload,
    format_preventive_plan_payload,
    format_service_ticket_payload,
    format_asset_request_payload,
    format_purchase_request_payload,
    format_purchase_order_payload,
    format_purchase_quotation_payload
)

def test_webhook_events_list():
    assert "MAINTENANCE_REQUESTED" in WEBHOOK_EVENTS
    assert "MAINTENANCE_ACCEPTED" in WEBHOOK_EVENTS
    assert "MAINTENANCE_REJECTED" in WEBHOOK_EVENTS
    assert "MAINTENANCE_COMPLETED" in WEBHOOK_EVENTS
    assert "MAINTENANCE_DELIVERED" in WEBHOOK_EVENTS
    assert "PREVENTIVE_PLAN_CREATED" in WEBHOOK_EVENTS
    assert "PREVENTIVE_ORDER_CREATED" in WEBHOOK_EVENTS
    assert "PREVENTIVE_ORDER_STARTED" in WEBHOOK_EVENTS
    assert "PREVENTIVE_ORDER_COMPLETED" in WEBHOOK_EVENTS
    assert "PREVENTIVE_ORDER_CANCELLED" in WEBHOOK_EVENTS
    assert "TICKET_CREATED" in WEBHOOK_EVENTS
    assert "TICKET_UPDATED" in WEBHOOK_EVENTS
    assert "TICKET_ASSIGNED" in WEBHOOK_EVENTS
    assert "TICKET_RESOLVED" in WEBHOOK_EVENTS
    assert "TICKET_CANCELLED" in WEBHOOK_EVENTS
    assert "TICKET_INTERACTION_ADDED" in WEBHOOK_EVENTS
    assert "ASSET_REQUEST_CREATED" in WEBHOOK_EVENTS
    assert "ASSET_REQUEST_APPROVED" in WEBHOOK_EVENTS
    assert "ASSET_REQUEST_REJECTED" in WEBHOOK_EVENTS
    assert "ASSET_REQUEST_DELIVERED" in WEBHOOK_EVENTS
    assert "PURCHASE_REQUEST_CREATED" in WEBHOOK_EVENTS
    assert "PURCHASE_REQUEST_APPROVED" in WEBHOOK_EVENTS
    assert "PURCHASE_REQUEST_REJECTED" in WEBHOOK_EVENTS
    assert "PURCHASE_QUOTATION_CREATED" in WEBHOOK_EVENTS
    assert "PURCHASE_ORDER_CREATED" in WEBHOOK_EVENTS
    assert "PURCHASE_ORDER_RECEIVED" in WEBHOOK_EVENTS

class DummyObj:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_format_maintenance_request_payload():
    solicitante = DummyObj(id=1, nome="Usuário Teste", email="user@test.com")
    tecnico = DummyObj(id=2, nome="Técnico Teste", email="tech@test.com")
    asset = DummyObj(id=10, nome="Notebook Dell", e_patrimonio="PAT-1234")
    
    sol = DummyObj(
        id=100,
        status="PENDENTE",
        prioridade="ALTA",
        descricao="Tela quebrada",
        observacao="Entregue na recepção",
        observacao_conclusao="Tela trocada",
        asset_id=10,
        asset=asset,
        solicitante_id=1,
        solicitante=solicitante,
        responsavel_id=2,
        responsavel=tecnico,
        data_solicitacao=None,
        data_conclusao=None
    )
    
    payload = format_maintenance_request_payload(sol, "MAINTENANCE_ACCEPTED")
    assert payload["event"] == "MAINTENANCE_ACCEPTED"
    assert payload["solicitacao_id"] == 100
    assert payload["tipo_manutencao"] == "CORRETIVA"
    assert payload["ativo"]["nome"] == "Notebook Dell"
    assert payload["ativo"]["patrimonio"] == "PAT-1234"
    assert payload["solicitante"]["nome"] == "Usuário Teste"
    assert payload["tecnico_responsavel"]["nome"] == "Técnico Teste"

def test_format_preventive_order_payload():
    tecnico = DummyObj(id=2, nome="Técnico Teste", email="tech@test.com")
    asset = DummyObj(id=10, nome="Ar Condicionado Split", e_patrimonio="PAT-5678")

    order = DummyObj(
        id=50,
        numero="OS-2026-00001",
        status="EM_ANDAMENTO",
        prioridade="ALTA",
        tipo="PREVENTIVA",
        observacoes="Limpeza mensal",
        custo_total=150.00,
        tempo_total_minutos=45,
        asset_id=10,
        asset=asset,
        tecnico_id=2,
        tecnico=tecnico,
        data_abertura=None,
        data_agendada=None,
        data_inicio=None,
        data_conclusao=None
    )

    payload = format_preventive_order_payload(order, "PREVENTIVE_ORDER_STARTED")
    assert payload["event"] == "PREVENTIVE_ORDER_STARTED"
    assert payload["os_id"] == 50
    assert payload["os_numero"] == "OS-2026-00001"
    assert payload["tipo_manutencao"] == "PREVENTIVA"
    assert payload["ativo"]["nome"] == "Ar Condicionado Split"
    assert payload["ativo"]["patrimonio"] == "PAT-5678"
    assert payload["tecnico_responsavel"]["nome"] == "Técnico Teste"

def test_format_service_ticket_payload():
    solicitante = DummyObj(id=1, nome="Maria Silva", email="maria@empresa.com")
    tecnico = DummyObj(id=5, nome="Carlos Técnico", email="carlos@empresa.com")
    categoria = DummyObj(id=2, nome="Sistemas / ERP")
    servico = DummyObj(id=15, nome="Erro de Login no ERP", categoria=categoria)

    ticket = DummyObj(
        id=301,
        codigo="CH-2026-00301",
        titulo="Usuário sem acesso ao módulo financeiro",
        status="Aberto",
        prioridade="Alta",
        descricao="Ao tentar logar, aparece a mensagem de erro 403.",
        solucao=None,
        servico_id=15,
        servico=servico,
        solicitante_id=1,
        solicitante=solicitante,
        tecnico_id=5,
        tecnico=tecnico,
        data_abertura=None,
        data_atualizacao=None,
        data_fechamento=None
    )

    interaction = DummyObj(
        id=99,
        tipo="Comentário",
        mensagem="Técnico assumiu o chamado e verificou as permissões no AD.",
        usuario=tecnico
    )

    payload = format_service_ticket_payload(ticket, "TICKET_INTERACTION_ADDED", interaction=interaction)
    assert payload["event"] == "TICKET_INTERACTION_ADDED"
    assert payload["ticket_id"] == 301
    assert payload["codigo"] == "CH-2026-00301"
    assert payload["servico"]["nome"] == "Erro de Login no ERP"
    assert payload["servico"]["categoria"] == "Sistemas / ERP"
    assert payload["solicitante"]["nome"] == "Maria Silva"
    assert payload["tecnico_responsavel"]["nome"] == "Carlos Técnico"
    assert payload["interacao"]["mensagem"] == "Técnico assumiu o chamado e verificou as permissões no AD."

def test_format_asset_request_payload():
    solicitante = DummyObj(id=2, nome="João Silva", email="joao@empresa.com")
    aprovador = DummyObj(id=1, nome="Admin Gerente", email="admin@empresa.com")
    asset = DummyObj(id=55, nome="MacBook Pro M2", e_patrimonio="PAT-9999")

    sol = DummyObj(
        id=77,
        status="Aprovada",
        motivo="Necessidade para projeto de desenvolvimento móvel.",
        asset_id=55,
        asset=asset,
        solicitante_id=2,
        solicitante=solicitante,
        aprovador_id=1,
        aprovador=aprovador,
        confirmador=None,
        confirmado_via_qr=False,
        observacao_entrega=None,
        data_solicitacao=None,
        data_aprovacao=None,
        data_prevista_devolucao=None,
        data_entrega=None
    )

    payload = format_asset_request_payload(sol, "ASSET_REQUEST_APPROVED")
    assert payload["event"] == "ASSET_REQUEST_APPROVED"
    assert payload["solicitacao_id"] == 77
    assert payload["status"] == "Aprovada"
    assert payload["ativo"]["nome"] == "MacBook Pro M2"
    assert payload["ativo"]["patrimonio"] == "PAT-9999"
    assert payload["solicitante"]["nome"] == "João Silva"
    assert payload["aprovador"]["nome"] == "Admin Gerente"

def test_format_purchase_request_payload():
    solicitante = DummyObj(id=10, nome="Ana Souza", email="ana@empresa.com")
    centro_custo = DummyObj(id=1, nome="TI Infraestrutura")
    product = DummyObj(id=5, nome="Switch Cisco 24p")
    item = DummyObj(product_id=5, product=product, quantidade=2.0, valor_estimado=1500.0, fornecedor_sugerido=None)

    req = DummyObj(
        id=200,
        numero="SC-2026-00200",
        status="Pendente",
        urgencia="Alta",
        justificativa="Substituição de switch danificado.",
        centro_custo=centro_custo,
        solicitante_id=10,
        solicitante=solicitante,
        itens=[item],
        data_criacao=None,
        data_necessaria=None
    )

    payload = format_purchase_request_payload(req, "PURCHASE_REQUEST_CREATED")
    assert payload["event"] == "PURCHASE_REQUEST_CREATED"
    assert payload["solicitacao_id"] == 200
    assert payload["numero"] == "SC-2026-00200"
    assert payload["total_estimado"] == 3000.0
    assert payload["solicitante"]["nome"] == "Ana Souza"
    assert payload["itens"][0]["produto_nome"] == "Switch Cisco 24p"



