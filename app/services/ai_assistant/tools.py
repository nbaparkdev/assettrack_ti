import json
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.transaction import Solicitacao, StatusSolicitacao, Movimentacao, TipoMovimentacao
from app.models.asset import Asset, AssetStatus
from app.models.user import User, UserRole
from app.models.maintenance import Manutencao, StatusManutencao, TipoManutencao, DestinoManutencao
from app.models.maintenance_request import SolicitacaoManutencao, StatusSolicitacaoManutencao
from datetime import datetime
from sqlalchemy import or_
from app.models.preventive_maintenance import MaintenanceOrder, MaintenancePlan, OrderStatus
from app.models.procurement import PurchaseRequest, PurchaseOrder, PurchaseRequestStatus, PurchaseOrderStatus, PurchaseProduct, MaterialStock

# ---------------------------------------------------------------------------
# TOOL FUNCTIONS
# ---------------------------------------------------------------------------

async def send_email_to_user(db: AsyncSession, user_id: int, target_email: str, subject: str, message: str, **kwargs) -> str:
    """Envia um e-mail para um usuário cadastrado no sistema."""
    from app.services.email_service import EmailService
    
    # Verify user exists
    stmt = select(User).where(User.email == target_email)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        return f"Erro: O e-mail '{target_email}' não pertence a nenhum usuário cadastrado na aplicação."
        
    user_nome = target_user.nome
    user_email = target_user.email
        
    email_svc = EmailService()
    try:
        success = await email_svc.send_notification(
            email_to=user_email,
            subject=subject,
            message=message,
            db=db
        )
        if success:
            return f"✅ E-mail enviado com sucesso para {user_nome} ({user_email})."
        else:
            return f"❌ Falha ao enviar e-mail para {user_nome} ({user_email}). Verifique os logs de erro ou as configurações SMTP."
    except Exception as e:
        return f"Erro ao enviar e-mail: {str(e)}"

async def get_my_active_tickets(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna um resumo das solicitações/tickets ativos do usuário."""
    stmt = (
        select(Solicitacao)
        .where(
            Solicitacao.solicitante_id == user_id,
            Solicitacao.status.in_([StatusSolicitacao.PENDENTE, StatusSolicitacao.APROVADA])
        )
        .order_by(Solicitacao.id.desc())
    )
    result = await db.execute(stmt)
    solicitacoes = result.scalars().all()
    
    if not solicitacoes:
        return "O usuário não tem nenhuma solicitação ativa no momento."
    
    resumo = f"Solicitações ativas do usuário (Total: {len(solicitacoes)}):\n"
    for s in solicitacoes:
        motivo = (s.motivo[:80] + "...") if s.motivo and len(s.motivo) > 80 else (s.motivo or "Sem descrição")
        data = s.data_solicitacao.strftime("%d/%m/%Y") if s.data_solicitacao else "?"
        resumo += f"  • Ticket #{s.id} | {s.status.value} | {data} | {motivo}\n"
    return resumo


async def search_all_tickets(db: AsyncSession, user_id: int, status_filter: str = "", **kwargs) -> str:
    """Retorna todos os tickets do sistema."""
    stmt = select(Solicitacao)
    if status_filter:
        try:
            enum_status = StatusSolicitacao(status_filter)
            stmt = stmt.where(Solicitacao.status == enum_status)
        except ValueError:
            pass
            
    stmt = stmt.order_by(Solicitacao.id.desc()).limit(20)
    result = await db.execute(stmt)
    solicitacoes = result.scalars().all()
    
    if not solicitacoes:
        return "Nenhum chamado encontrado no sistema."
    
    # Contadores
    total_stmt = select(func.count(Solicitacao.id))
    total = await db.scalar(total_stmt)
        
    resumo = f"Chamados no sistema (mostrando últimos {len(solicitacoes)} de {total} total):\n"
    for s in solicitacoes:
        motivo = (s.motivo[:60] + "...") if s.motivo and len(s.motivo) > 60 else (s.motivo or "Sem descrição")
        data = s.data_solicitacao.strftime("%d/%m/%Y") if s.data_solicitacao else "?"
        resumo += f"  • Ticket #{s.id} | {s.status.value} | {data} | {motivo}\n"
    return resumo


async def search_assets(db: AsyncSession, user_id: int, query: str = "", **kwargs) -> str:
    """Busca ativos no sistema por nome, patrimônio ou modelo."""
    stmt = select(Asset)
    if query:
        stmt = stmt.where(or_(
            Asset.nome.ilike(f"%{query}%"),
            Asset.e_patrimonio.ilike(f"%{query}%"),
            Asset.modelo.ilike(f"%{query}%"),
            Asset.numero_serie.ilike(f"%{query}%")
        ))
    stmt = stmt.order_by(Asset.id.desc()).limit(15)
    result = await db.execute(stmt)
    assets = result.scalars().all()
    
    if not assets:
        return f"Nenhum ativo encontrado{' para o termo: ' + query if query else ''}."
    
    total_stmt = select(func.count(Asset.id))
    if query:
        total_stmt = total_stmt.where(or_(
            Asset.nome.ilike(f"%{query}%"),
            Asset.e_patrimonio.ilike(f"%{query}%"),
            Asset.modelo.ilike(f"%{query}%")
        ))
    total = await db.scalar(total_stmt)
        
    resumo = f"Ativos encontrados (mostrando {len(assets)} de {total} total):\n"
    for a in assets:
        status_val = a.status.value if a.status else "Desconhecido"
        modelo = a.modelo or "N/A"
        posse = a.em_posse_de or "Sem responsável"
        resumo += f"  • {a.nome} | Patrimônio: {a.e_patrimonio} | Modelo: {modelo} | Status: {status_val} | Posse: {posse}\n"
    return resumo


async def get_system_overview(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna um panorama geral completo do sistema."""
    # Total de ativos por status
    assets_by_status = {}
    for status in AssetStatus:
        count = await db.scalar(
            select(func.count(Asset.id)).where(Asset.status == status)
        )
        if count and count > 0:
            assets_by_status[status.value] = count
    total_assets = sum(assets_by_status.values()) if assets_by_status else 0
    
    # Total de chamados por status
    tickets_by_status = {}
    for status in StatusSolicitacao:
        count = await db.scalar(
            select(func.count(Solicitacao.id)).where(Solicitacao.status == status)
        )
        if count and count > 0:
            tickets_by_status[status.value] = count
    total_tickets = sum(tickets_by_status.values()) if tickets_by_status else 0
    
    # Manutenções
    manut_andamento = await db.scalar(
        select(func.count(Manutencao.id)).where(Manutencao.status == StatusManutencao.EM_ANDAMENTO)
    ) or 0
    manut_concluidas = await db.scalar(
        select(func.count(Manutencao.id)).where(Manutencao.status == StatusManutencao.CONCLUIDA)
    ) or 0
    
    # Solicitações de manutenção pendentes
    sol_manut_pendentes = await db.scalar(
        select(func.count(SolicitacaoManutencao.id)).where(
            SolicitacaoManutencao.status == StatusSolicitacaoManutencao.PENDENTE
        )
    ) or 0
    
    # Total de usuários
    total_users = await db.scalar(select(func.count(User.id))) or 0
    
    # Últimos 5 chamados
    stmt_recentes = select(Solicitacao).order_by(Solicitacao.id.desc()).limit(5)
    result_recentes = await db.execute(stmt_recentes)
    recentes = result_recentes.scalars().all()
    
    resumo = "=== PANORAMA GERAL DO SISTEMA ===\n\n"
    
    resumo += f"👥 Total de Usuários: {total_users}\n\n"
    
    resumo += f"📦 Ativos cadastrados: {total_assets}\n"
    if assets_by_status:
        for status_name, count in assets_by_status.items():
            resumo += f"   - {status_name}: {count}\n"
    
    resumo += f"\n📋 Chamados/Solicitações: {total_tickets}\n"
    if tickets_by_status:
        for status_name, count in tickets_by_status.items():
            resumo += f"   - {status_name}: {count}\n"
    else:
        resumo += "   - Nenhum chamado registrado.\n"
    
    resumo += f"\n🔧 Manutenções em andamento: {manut_andamento}\n"
    resumo += f"✅ Manutenções concluídas: {manut_concluidas}\n"
    resumo += f"⏳ Solicitações de manutenção pendentes: {sol_manut_pendentes}\n"
    
    resumo += "\n📌 Últimos chamados:\n"
    if recentes:
        for s in recentes:
            motivo = (s.motivo[:60] + "...") if s.motivo and len(s.motivo) > 60 else (s.motivo or "Sem descrição")
            data = s.data_solicitacao.strftime("%d/%m/%Y %H:%M") if s.data_solicitacao else "?"
            resumo += f"   - Ticket #{s.id} | {s.status.value} | {data} | {motivo}\n"
    else:
        resumo += "   - Nenhum chamado recente.\n"
    
    return resumo


async def get_maintenance_report(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna relatório detalhado de manutenções."""
    # Em andamento
    stmt_andamento = (
        select(Manutencao)
        .options(selectinload(Manutencao.asset))
        .where(Manutencao.status == StatusManutencao.EM_ANDAMENTO)
        .order_by(Manutencao.data_entrada.desc())
        .limit(10)
    )
    result = await db.execute(stmt_andamento)
    em_andamento = result.scalars().all()
    
    # Últimas concluídas
    stmt_concluidas = (
        select(Manutencao)
        .options(selectinload(Manutencao.asset))
        .where(Manutencao.status == StatusManutencao.CONCLUIDA)
        .order_by(Manutencao.data_conclusao.desc())
        .limit(5)
    )
    result2 = await db.execute(stmt_concluidas)
    concluidas = result2.scalars().all()
    
    resumo = "=== RELATÓRIO DE MANUTENÇÕES ===\n\n"
    
    resumo += f"🔧 Em andamento ({len(em_andamento)}):\n"
    if em_andamento:
        for m in em_andamento:
            asset_nome = m.asset.nome if m.asset else "Ativo desconhecido"
            patrimonio = m.asset.e_patrimonio if m.asset else "?"
            data = m.data_entrada.strftime("%d/%m/%Y") if m.data_entrada else "?"
            tipo = m.tipo.value if m.tipo else "?"
            custo = f"R$ {m.custo:.2f}" if m.custo else "Sem custo"
            resumo += f"   - OS #{m.id} | {asset_nome} ({patrimonio}) | {tipo} | Entrada: {data} | {custo}\n"
            resumo += f"     Motivo: {m.motivo[:80]}...\n" if len(m.motivo or "") > 80 else f"     Motivo: {m.motivo or 'N/A'}\n"
    else:
        resumo += "   Nenhuma manutenção em andamento.\n"
    
    resumo += f"\n✅ Últimas concluídas ({len(concluidas)}):\n"
    if concluidas:
        for m in concluidas:
            asset_nome = m.asset.nome if m.asset else "Ativo desconhecido"
            data_c = m.data_conclusao.strftime("%d/%m/%Y") if m.data_conclusao else "?"
            custo = f"R$ {m.custo:.2f}" if m.custo else "Sem custo"
            resumo += f"   - OS #{m.id} | {asset_nome} | Concluída: {data_c} | {custo}\n"
    else:
        resumo += "   Nenhuma manutenção concluída recentemente.\n"
    
    return resumo


async def get_assets_by_status(db: AsyncSession, user_id: int, status: str = "", **kwargs) -> str:
    """Lista ativos filtrados por status específico."""
    stmt = select(Asset)
    if status:
        try:
            enum_status = AssetStatus(status)
            stmt = stmt.where(Asset.status == enum_status)
        except ValueError:
            return f"Status inválido: {status}. Use: Disponível, Em uso, Manutenção, Armazenado, Baixado."
    
    stmt = stmt.order_by(Asset.id.desc()).limit(20)
    result = await db.execute(stmt)
    assets = result.scalars().all()
    
    if not assets:
        return f"Nenhum ativo encontrado com status: {status or 'todos'}."
    
    resumo = f"Ativos{' com status ' + status if status else ''} (mostrando {len(assets)}):\n"
    for a in assets:
        status_val = a.status.value if a.status else "?"
        posse = a.em_posse_de or "Livre"
        resumo += f"  • {a.nome} | Pat: {a.e_patrimonio} | {status_val} | Posse: {posse}\n"
    return resumo


async def create_service_desk_ticket(db: AsyncSession, user_id: int, title: str, description: str, **kwargs) -> str:
    """Cria um novo chamado de TI para o usuário."""
    nova_solicitacao = Solicitacao(
        solicitante_id=user_id,
        status=StatusSolicitacao.PENDENTE,
        data_solicitacao=datetime.now(),
        motivo=f"{title}: {description}",
    )
    db.add(nova_solicitacao)
    await db.commit()
    await db.refresh(nova_solicitacao)
    return f"✅ Chamado #{nova_solicitacao.id} criado com sucesso! Status: Pendente."


async def get_preventive_maintenance_orders(db: AsyncSession, user_id: int, status: str = "", **kwargs) -> str:
    """Retorna ordens de manutenção preventiva."""
    stmt = select(MaintenanceOrder).options(selectinload(MaintenanceOrder.asset), selectinload(MaintenanceOrder.plan))
    if status:
        stmt = stmt.where(MaintenanceOrder.status == status)
    stmt = stmt.order_by(MaintenanceOrder.id.desc()).limit(15)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    if not orders:
        return "Nenhuma ordem de manutenção preventiva encontrada."
        
    resumo = "=== ORDENS DE MANUTENÇÃO PREVENTIVA ===\n\n"
    for o in orders:
        data_abertura = o.data_abertura.strftime("%d/%m/%Y") if o.data_abertura else "?"
        asset_name = o.asset.nome if o.asset else (o.infra_predial_servico or "N/A")
        plan_name = o.plan.nome if o.plan else "Sem Plano"
        resumo += f" - OS Preventiva #{o.id} | Status: {o.status.value if o.status else '?'} | Ativo: {asset_name} | Plano: {plan_name} | Abertura: {data_abertura}\n"
    return resumo

async def get_purchase_requests(db: AsyncSession, user_id: int, status: str = "", **kwargs) -> str:
    """Retorna requisições de compras."""
    stmt = select(PurchaseRequest)
    if status:
        stmt = stmt.where(PurchaseRequest.status == status)
    stmt = stmt.order_by(PurchaseRequest.id.desc()).limit(15)
    result = await db.execute(stmt)
    reqs = result.scalars().all()
    
    if not reqs:
        return "Nenhuma requisição de compra encontrada."
        
    resumo = "=== REQUIÇÕES DE COMPRAS ===\n\n"
    for r in reqs:
        data_criacao = r.data_criacao.strftime("%d/%m/%Y") if r.data_criacao else "?"
        resumo += f" - Req #{r.id} ({r.numero}) | Status: {r.status.value if r.status else '?'} | Urgência: {r.urgencia} | Criada: {data_criacao}\n"
        resumo += f"   Justificativa: {r.justificativa[:80]}...\n"
    return resumo

async def get_purchase_orders(db: AsyncSession, user_id: int, status: str = "", **kwargs) -> str:
    """Retorna pedidos de compras (POs)."""
    stmt = select(PurchaseOrder).options(selectinload(PurchaseOrder.fornecedor))
    if status:
        stmt = stmt.where(PurchaseOrder.status == status)
    stmt = stmt.order_by(PurchaseOrder.id.desc()).limit(15)
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    if not orders:
        return "Nenhum pedido de compra encontrado."
        
    resumo = "=== PEDIDOS DE COMPRA (POs) ===\n\n"
    for o in orders:
        data_emissao = o.data_emissao.strftime("%d/%m/%Y") if o.data_emissao else "?"
        forn_nome = o.fornecedor.nome_fantasia if o.fornecedor else "Desconhecido"
        resumo += f" - PO #{o.id} ({o.numero}) | Fornecedor: {forn_nome} | Status: {o.status.value if o.status else '?'} | Valor: R$ {o.valor_total:.2f} | Emissão: {data_emissao}\n"
    return resumo

async def create_asset(db: AsyncSession, user_id: int, nome: str, e_patrimonio: str, modelo: str = None, descricao: str = None, numero_serie: str = None, valor: float = None, status: str = "Disponível", **kwargs) -> str:
    """Cria um novo ativo no sistema."""
    stmt = select(Asset).where(Asset.e_patrimonio == e_patrimonio)
    existing = await db.scalar(stmt)
    if existing:
        return f"Erro: Já existe um ativo cadastrado com o patrimônio '{e_patrimonio}'."
    
    try:
        status_enum = AssetStatus(status)
    except ValueError:
        status_enum = AssetStatus.DISPONIVEL

    novo = Asset(
        nome=nome,
        e_patrimonio=e_patrimonio,
        modelo=modelo,
        descricao=descricao,
        numero_serie=numero_serie,
        valor=valor,
        status=status_enum,
        created_by_id=user_id
    )
    db.add(novo)
    await db.commit()
    await db.refresh(novo)
    return f"✅ Ativo '{nome}' (Patrimônio: {e_patrimonio}) cadastrado com sucesso com ID #{novo.id}."

async def update_asset(db: AsyncSession, user_id: int, asset_id: int, nome: str = None, modelo: str = None, descricao: str = None, numero_serie: str = None, valor: float = None, status: str = None, em_posse_de: str = None, **kwargs) -> str:
    """Atualiza dados de um ativo existente."""
    stmt = select(Asset).where(Asset.id == asset_id)
    asset = await db.scalar(stmt)
    if not asset:
        return f"Erro: Ativo com ID #{asset_id} não encontrado."
    
    if nome is not None: asset.nome = nome
    if modelo is not None: asset.modelo = modelo
    if descricao is not None: asset.descricao = descricao
    if numero_serie is not None: asset.numero_serie = numero_serie
    if valor is not None: asset.valor = valor
    if em_posse_de is not None: asset.em_posse_de = em_posse_de
    
    if status is not None:
        try:
            asset.status = AssetStatus(status)
        except ValueError:
            pass

    await db.commit()
    return f"✅ Ativo ID #{asset_id} ({asset.nome}) atualizado com sucesso."

async def deactivate_asset(db: AsyncSession, user_id: int, asset_id: int, **kwargs) -> str:
    """Desativa de forma lógica um ativo marcando-o como Baixado e bloqueado."""
    stmt = select(Asset).where(Asset.id == asset_id)
    asset = await db.scalar(stmt)
    if not asset:
        return f"Erro: Ativo com ID #{asset_id} não encontrado."
    
    asset.status = AssetStatus.BAIXADO
    asset.bloqueado = True
    await db.commit()
    return f"✅ Ativo ID #{asset_id} ({asset.nome}) desativado com sucesso (Status: Baixado e Bloqueado)."

async def update_ticket_status(db: AsyncSession, user_id: int, ticket_id: int, status: str, observacao: str = None, **kwargs) -> str:
    """Aprova, rejeita ou cancela um chamado (ticket) do sistema."""
    stmt = select(Solicitacao).where(Solicitacao.id == ticket_id)
    ticket = await db.scalar(stmt)
    if not ticket:
        return f"Erro: Chamado ID #{ticket_id} não encontrado."
    
    try:
        status_enum = StatusSolicitacao(status)
    except ValueError:
        return f"Erro: Status inválido '{status}'. Use: Pendente, Aprovada, Entregue, Rejeitada, Cancelada."

    ticket.status = status_enum
    ticket.aprovador_id = user_id
    ticket.data_aprovacao = datetime.now()
    if observacao:
        ticket.observacao_entrega = observacao

    await db.commit()
    return f"✅ Status do Chamado ID #{ticket_id} alterado com sucesso para '{status_enum.value}'."

async def create_maintenance(db: AsyncSession, user_id: int, asset_id: int, motivo: str, tipo: str = "corretiva", **kwargs) -> str:
    """Envia um ativo para manutenção, abrindo uma Ordem de Serviço."""
    stmt = select(Asset).where(Asset.id == asset_id)
    asset = await db.scalar(stmt)
    if not asset:
        return f"Erro: Ativo ID #{asset_id} não encontrado."
    
    try:
        tipo_enum = TipoManutencao(tipo)
    except ValueError:
        tipo_enum = TipoManutencao.CORRETIVA

    nova_os = Manutencao(
        asset_id=asset_id,
        responsavel_id=user_id,
        motivo=motivo,
        tipo=tipo_enum,
        status=StatusManutencao.EM_ANDAMENTO,
        data_entrada=datetime.now()
    )
    asset.status = AssetStatus.MANUTENCAO
    db.add(nova_os)
    await db.commit()
    await db.refresh(nova_os)
    return f"✅ OS #{nova_os.id} aberta com sucesso. Ativo '{asset.nome}' alterado para status 'Manutenção'."

async def complete_maintenance(db: AsyncSession, user_id: int, os_id: int, observacao_conclusao: str = None, custo: float = None, **kwargs) -> str:
    """Conclui uma ordem de serviço de manutenção."""
    stmt = select(Manutencao).options(selectinload(Manutencao.asset)).where(Manutencao.id == os_id)
    os = await db.scalar(stmt)
    if not os:
        return f"Erro: Ordem de Serviço #{os_id} não encontrada."
    
    os.status = StatusManutencao.CONCLUIDA
    os.data_conclusao = datetime.now()
    if observacao_conclusao:
        os.observacao_conclusao = observacao_conclusao
    if custo is not None:
        os.custo = custo

    if os.asset:
        os.asset.status = AssetStatus.DISPONIVEL

    await db.commit()
    return f"✅ OS #{os_id} concluída com sucesso. O ativo retornou ao status 'Disponível'."

async def create_user(db: AsyncSession, user_id: int, email: str, nome: str, role: str = "usuario_comum", matricula: str = None, cargo: str = None, **kwargs) -> str:
    """Cria um novo usuário no sistema."""
    from app.crud.user import user as user_crud
    
    stmt = select(User).where(User.email == email)
    existing = await db.scalar(stmt)
    if existing:
        return f"Erro: Já existe um usuário cadastrado com o e-mail '{email}'."

    try:
        role_enum = UserRole(role)
    except ValueError:
        role_enum = UserRole.USUARIO

    novo_user = User(
        email=email,
        nome=nome,
        role=role_enum,
        matricula=matricula,
        cargo=cargo,
        hashed_password=user_crud.get_password_hash("123456"),
        is_active=True
    )
    db.add(novo_user)
    await db.commit()
    await db.refresh(novo_user)
    return f"✅ Usuário '{nome}' ({email}) cadastrado com sucesso com perfil '{role_enum.value}'."

async def deactivate_user(db: AsyncSession, user_id: int, user_to_deactivate_id: int, **kwargs) -> str:
    """Desativa de forma lógica um usuário do sistema (is_active=False)."""
    stmt = select(User).where(User.id == user_to_deactivate_id)
    target = await db.scalar(stmt)
    if not target:
        return f"Erro: Usuário com ID #{user_to_deactivate_id} não encontrado."
    
    target.is_active = False
    await db.commit()
    return f"✅ Usuário '{target.nome}' (ID: #{user_to_deactivate_id}) desativado com sucesso."
async def list_departments(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna todos os departamentos cadastrados no sistema."""
    from app.models.location import Departamento
    stmt = select(Departamento).order_by(Departamento.nome)
    result = await db.execute(stmt)
    deps = result.scalars().all()
    if not deps:
        return "Nenhum departamento cadastrado."
    res = "=== DEPARTAMENTOS CADASTRADOS ===\n"
    for d in deps:
        res += f"  • ID #{d.id} | {d.nome}\n"
    return res

async def list_locations(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna todas as localizações/locais físicos cadastrados no sistema."""
    from app.models.location import Localizacao
    stmt = select(Localizacao).options(selectinload(Localizacao.departamento)).order_by(Localizacao.nome)
    result = await db.execute(stmt)
    locs = result.scalars().all()
    if not locs:
        return "Nenhuma localização cadastrada."
    res = "=== LOCALIZAÇÕES CADASTRADAS ===\n"
    for l in locs:
        dep_nome = l.departamento.nome if l.departamento else "Sem Departamento"
        res += f"  • ID #{l.id} | {l.nome} ({dep_nome})\n"
    return res

async def list_categories(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna todas as categorias de ativos cadastradas no sistema."""
    from app.models.asset_category import AssetCategory
    stmt = select(AssetCategory).order_by(AssetCategory.nome)
    result = await db.execute(stmt)
    cats = result.scalars().all()
    if not cats:
        return "Nenhuma categoria cadastrada."
    res = "=== CATEGORIAS DE ATIVOS ===\n"
    for c in cats:
        res += f"  • ID #{c.id} | {c.nome} - {c.descricao or ''}\n"
    return res

async def list_suppliers(db: AsyncSession, user_id: int, **kwargs) -> str:
    """Retorna todos os fornecedores cadastrados no sistema."""
    from app.models.supplier import Fornecedor
    stmt = select(Fornecedor).order_by(Fornecedor.nome)
    result = await db.execute(stmt)
    forns = result.scalars().all()
    if not forns:
        return "Nenhum fornecedor cadastrado."
    res = "=== FORNECEDORES CADASTRADOS ===\n"
    for f in forns:
        res += f"  • ID #{f.id} | {f.nome} (CNPJ: {f.cnpj or 'N/A'})\n"
    return res

async def search_users(db: AsyncSession, user_id: int, query: str = "", **kwargs) -> str:
    """Busca usuários do sistema por nome, e-mail ou matrícula."""
    stmt = select(User)
    if query:
        stmt = stmt.where(or_(
            User.nome.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%"),
            User.matricula.ilike(f"%{query}%")
        ))
    stmt = stmt.order_by(User.id.desc()).limit(15)
    result = await db.execute(stmt)
    users = result.scalars().all()
    if not users:
        return "Nenhum usuário encontrado."
    res = f"=== USUÁRIOS ENCONTRADOS (mostrando {len(users)}) ===\n"
    for u in users:
        status_val = "Ativo" if u.is_active else "Inativo"
        res += f"  • ID #{u.id} | {u.nome} ({u.email}) | Perfil: {u.role.value} | Status: {status_val}\n"
    return res

async def read_system_manual(db: AsyncSession, user_id: int, document_name: str = "manual_do_usuario", **kwargs) -> str:
    """Retorna o conteúdo do manual ou guia do sistema selecionado."""
    import os
    
    docs_dir = "/home/humberto/Aplicativos/Assettrackti/assettrack_ti/docs"
    
    mapping = {
        "manual_do_usuario": "MANUAL_DO_USUARIO.md",
        "funcionalidades": "FUNCIONALIDADES.md",
        "api": "API_DOCS.md",
        "service_desk": "MELHORIAS_SERVICE_DESK.md",
        "resolucoes_tecnicas": "RESOLUCOES_TECNICAS.md"
    }
    
    doc_file = mapping.get(document_name.lower())
    if not doc_file:
        return f"Erro: Documento '{document_name}' não encontrado. Escolha entre: manual_do_usuario, funcionalidades, api, service_desk, resolucoes_tecnicas."
        
    file_path = os.path.join(docs_dir, doc_file)
    if not os.path.exists(file_path):
        return f"Erro: O arquivo {doc_file} não foi encontrado no servidor."
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return f"=== DOCUMENTO: {doc_file} ===\n\n{content}"
    except Exception as e:
        return f"Erro ao ler o documento: {str(e)}"


# ---------------------------------------------------------------------------
# TOOL REGISTRY
# ---------------------------------------------------------------------------

AVAILABLE_TOOLS = {
    "get_my_active_tickets": {
        "description": "Busca todas as solicitações e tickets ativos/pendentes do usuário logado.",
        "func": get_my_active_tickets,
        "advanced": False,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_system_overview": {
        "description": "Retorna panorama completo do sistema: total de ativos por status, chamados por status, manutenções em andamento, solicitações pendentes, e últimos chamados. USE SEMPRE que perguntarem sobre o estado geral, resumo, ou panorama do sistema.",
        "func": get_system_overview,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_maintenance_report": {
        "description": "Retorna relatório detalhado de manutenções: ordens de serviço em andamento com ativo, tipo e custo; e últimas concluídas. USE quando perguntarem sobre manutenções, ordens de serviço, reparos.",
        "func": get_maintenance_report,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "search_all_tickets": {
        "description": "Lista os últimos chamados/tickets de todos os usuários do sistema. USE quando perguntarem sobre chamados, tickets, solicitações existentes.",
        "func": search_all_tickets,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "description": "Filtro de status: Pendente, Aprovada, Entregue, Rejeitada, Cancelada."
                }
            },
            "required": []
        }
    },
    "search_assets": {
        "description": "Busca e lista ativos, computadores, equipamentos ou patrimônios. Pode buscar por nome, número de patrimônio, modelo ou série. Sem query lista todos. USE quando perguntarem sobre ativos, equipamentos, patrimônio, computadores, impressoras.",
        "func": search_assets,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termo para buscar (ex: notebook, IMP-001). Deixe vazio para listar todos."
                }
            },
            "required": []
        }
    },
    "get_assets_by_status": {
        "description": "Lista ativos filtrados por status: Disponível, Em uso, Manutenção, Armazenado, Baixado. USE quando perguntarem sobre ativos disponíveis, em uso, etc.",
        "func": get_assets_by_status,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Status do ativo: Disponível, Em uso, Manutenção, Armazenado, Baixado."
                }
            },
            "required": []
        }
    },
    "create_service_desk_ticket": {
        "description": "Abre/cria um novo chamado ou ticket de suporte de TI para o usuário logado.",
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
                    "description": "Descrição detalhada do problema."
                }
            },
            "required": ["title", "description"]
        }
    },
    "get_preventive_maintenance_orders": {
        "description": "Busca ordens de serviço de manutenção preventiva. USE quando perguntarem sobre manutenções preventivas, agendamentos, etc.",
        "func": get_preventive_maintenance_orders,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filtro opcional de status da OS."
                }
            },
            "required": []
        }
    },
    "get_purchase_requests": {
        "description": "Busca requisições de compras cadastradas. USE quando perguntarem sobre solicitações de compras, requisições, etc.",
        "func": get_purchase_requests,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filtro opcional de status (Ex: Rascunho, Pendente, Aprovada, etc)."
                }
            },
            "required": []
        }
    },
    "get_purchase_orders": {
        "description": "Busca pedidos de compra (POs) emitidos para fornecedores. USE quando perguntarem sobre pedidos de compra, POs, ordens de compra.",
        "func": get_purchase_orders,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filtro opcional de status (Ex: Aberto, Enviado, Aceito, Recebido total)."
                }
            },
            "required": []
        }
    },
    "send_email_to_user": {
        "description": "Envia um e-mail para um usuário CADASTRADO no sistema. USE quando solicitar envio de relatórios, avisos ou mensagens por e-mail para outro funcionário.",
        "func": send_email_to_user,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "target_email": {
                    "type": "string",
                    "description": "E-mail do destinatário. Deve obrigatoriamente estar cadastrado no sistema."
                },
                "subject": {
                    "type": "string",
                    "description": "Assunto do e-mail."
                },
                "message": {
                    "type": "string",
                    "description": "Corpo do e-mail."
                }
            },
            "required": ["target_email", "subject", "message"]
        }
    },
    "create_asset": {
        "description": "Cadastra/cria um novo ativo (equipamento, notebook, etc) no sistema. Disponível apenas para administradores.",
        "func": create_asset,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "nome": {
                    "type": "string",
                    "description": "Nome do ativo (ex: Notebook Dell Vostro 3520)."
                },
                "e_patrimonio": {
                    "type": "string",
                    "description": "Número do patrimônio exclusivo (ex: PAT-00445)."
                },
                "modelo": {
                    "type": "string",
                    "description": "Modelo do equipamento."
                },
                "descricao": {
                    "type": "string",
                    "description": "Breve descrição."
                },
                "numero_serie": {
                    "type": "string",
                    "description": "Número de série."
                },
                "valor": {
                    "type": "number",
                    "description": "Valor monetário do ativo."
                },
                "status": {
                    "type": "string",
                    "description": "Status do ativo (ex: Disponível, Armazenado)."
                }
            },
            "required": ["nome", "e_patrimonio"]
        }
    },
    "update_asset": {
        "description": "Atualiza dados de um ativo existente. Disponível apenas para administradores.",
        "func": update_asset,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "integer",
                    "description": "ID numérico do ativo."
                },
                "nome": {
                    "type": "string",
                    "description": "Novo nome."
                },
                "modelo": {
                    "type": "string",
                    "description": "Novo modelo."
                },
                "descricao": {
                    "type": "string",
                    "description": "Nova descrição."
                },
                "numero_serie": {
                    "type": "string",
                    "description": "Novo número de série."
                },
                "valor": {
                    "type": "number",
                    "description": "Novo valor."
                },
                "status": {
                    "type": "string",
                    "description": "Novo status (Disponível, Em uso, Manutenção, Armazenado, Baixado)."
                },
                "em_posse_de": {
                    "type": "string",
                    "description": "Nome da pessoa em posse do ativo."
                }
            },
            "required": ["asset_id"]
        }
    },
    "deactivate_asset": {
        "description": "Desativa de forma lógica (baixa) um ativo do sistema, marcando-o como Baixado e bloqueado. Disponível apenas para administradores.",
        "func": deactivate_asset,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "integer",
                    "description": "ID numérico do ativo a ser desativado."
                }
            },
            "required": ["asset_id"]
        }
    },
    "update_ticket_status": {
        "description": "Altera o status de um chamado/solicitação (Aprova, rejeita ou cancela). Disponível apenas para administradores.",
        "func": update_ticket_status,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {
                    "type": "integer",
                    "description": "ID numérico do chamado/solicitação."
                },
                "status": {
                    "type": "string",
                    "description": "Novo status: Pendente, Aprovada, Entregue, Rejeitada, Cancelada."
                },
                "observacao": {
                    "type": "string",
                    "description": "Observação opcional sobre a mudança de status."
                }
            },
            "required": ["ticket_id", "status"]
        }
    },
    "create_maintenance": {
        "description": "Abre uma Ordem de Serviço de manutenção para um ativo, mudando seu status para 'Manutenção'. Disponível apenas para administradores.",
        "func": create_maintenance,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {
                    "type": "integer",
                    "description": "ID do ativo a ser enviado para manutenção."
                },
                "motivo": {
                    "type": "string",
                    "description": "Descrição do defeito/motivo da manutenção."
                },
                "tipo": {
                    "type": "string",
                    "description": "Tipo: preventiva, corretiva, upgrade, outro."
                }
            },
            "required": ["asset_id", "motivo"]
        }
    },
    "complete_maintenance": {
        "description": "Conclui uma OS de manutenção existente, retornando o ativo para o status 'Disponível'. Disponível apenas para administradores.",
        "func": complete_maintenance,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "os_id": {
                    "type": "integer",
                    "description": "ID numérico da Ordem de Serviço."
                },
                "observacao_conclusao": {
                    "type": "string",
                    "description": "Descrição dos reparos executados."
                },
                "custo": {
                    "type": "number",
                    "description": "Custo total do serviço."
                }
            },
            "required": ["os_id"]
        }
    },
    "create_user": {
        "description": "Cria um novo usuário com perfil específico no sistema. Disponível apenas para administradores.",
        "func": create_user,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "E-mail exclusivo do novo usuário."
                },
                "nome": {
                    "type": "string",
                    "description": "Nome completo."
                },
                "role": {
                    "type": "string",
                    "description": "Perfil: admin, gerente_ti, tecnico, gerente_infra, comprador, usuario_comum, rh."
                },
                "matricula": {
                    "type": "string",
                    "description": "Matrícula."
                },
                "cargo": {
                    "type": "string",
                    "description": "Cargo ou função."
                }
            },
            "required": ["email", "nome"]
        }
    },
    "deactivate_user": {
        "description": "Desativa de forma lógica (is_active=False) um usuário do sistema. Disponível apenas para administradores.",
        "func": deactivate_user,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "user_to_deactivate_id": {
                    "type": "integer",
                    "description": "ID numérico do usuário a ser desativado."
                }
            },
            "required": ["user_to_deactivate_id"]
        }
    },
    "list_departments": {
        "description": "Lista todos os departamentos cadastrados (ex: TI, Compras, RH) com seus IDs correspondentes. USE antes de associar um usuário a um departamento.",
        "func": list_departments,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "list_locations": {
        "description": "Lista todas as localizações/locais físicos cadastrados (ex: Almoxarifado, Sala 101) com seus IDs. USE antes de associar ou movimentar um ativo para uma localização.",
        "func": list_locations,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "list_categories": {
        "description": "Lista todas as categorias de ativos cadastradas no sistema (ex: Notebook, Servidor, Mouse) com seus IDs. USE antes de cadastrar/criar um ativo para encontrar a categoria correta.",
        "func": list_categories,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "list_suppliers": {
        "description": "Lista todos os fornecedores cadastrados no sistema com seus IDs. USE antes de associar um ativo a um fornecedor no cadastro.",
        "func": list_suppliers,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "search_users": {
        "description": "Busca usuários cadastrados no sistema por nome, e-mail ou matrícula. USE para encontrar o ID correto de um usuário antes de desativá-lo ou transferir posses.",
        "func": search_users,
        "advanced": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Termo de busca (nome, e-mail ou matrícula). Deixe vazio para listar recentes."
                }
            },
            "required": []
        }
    },
    "read_system_manual": {
        "description": "Busca informações, guias, instruções operacionais e ajuda nos manuais e guias oficiais do AssetTrack TI. USE sempre que o usuário perguntar como fazer algo no sistema, o que significa um termo, como funciona um fluxo (compras, chamados, termos, qr code, perfis, permissões) ou como usar as telas.",
        "func": read_system_manual,
        "advanced": False,
        "parameters": {
            "type": "object",
            "properties": {
                "document_name": {
                    "type": "string",
                    "description": "Nome do documento a ler. Escolha entre: manual_do_usuario, funcionalidades, api, service_desk, resolucoes_tecnicas. Padrão: manual_do_usuario."
                }
            },
            "required": []
        }
    }
}


# ---------------------------------------------------------------------------
# SCHEMA GENERATORS
# ---------------------------------------------------------------------------

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


def get_tools_summary(allow_advanced: bool = False) -> str:
    """Returns a human-readable summary of available tools for the system prompt."""
    lines = []
    for name, metadata in AVAILABLE_TOOLS.items():
        if metadata.get("advanced", False) and not allow_advanced:
            continue
        lines.append(f"- {name}: {metadata['description']}")
    return "\n".join(lines)


async def execute_tool(db: AsyncSession, user_id: int, tool_name: str, arguments_json: str) -> str:
    if tool_name not in AVAILABLE_TOOLS:
        return f"Erro: Ferramenta {tool_name} não encontrada."
    
    try:
        kwargs = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError:
        kwargs = {}
        
    func = AVAILABLE_TOOLS[tool_name]["func"]
    try:
        result = await func(db=db, user_id=user_id, **kwargs)
        return str(result)
    except Exception as e:
        import traceback
        return f"Erro ao executar {tool_name}: {str(e)}\n{traceback.format_exc()}"


def clean_unwanted_tool_tags(text: str) -> str:
    """Limpa qualquer tag de ferramenta ou colchete residual da resposta final enviada ao usuário."""
    if not text:
        return ""
    import re
    # 1. Remove tags como [CALL: nome_ferramenta ...] ou [nome_ferramenta ...] ou [nome_ferramenta {} - ...]
    cleaned = re.sub(r'\[(?:CALL:\s*)?[a-zA-Z0-9_]+(?:\s+[^\]]*)?\]', '', text)
    # 2. Limpa fragmentos de descrições em inglês isoladas que o modelo possa ter colado
    cleaned = re.sub(r'\s*-\s*(?:Number|List|Search|Get|Returns)[a-zA-Z0-9\s,\.\-]+\.?\s*', ' ', cleaned)
    # 3. Limpa colchetes isolados restantes como [ID] ou [Status]
    cleaned = re.sub(r'\[[a-zA-Z0-9_]+\]', '', cleaned)
    # 4. Limpa múltiplos espaços e quebras de linha excessivas
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    return cleaned.strip()
