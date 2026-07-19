# app/web/endpoints/rh.py
import os
from typing import Annotated, Optional, List
from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException, status, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.asset import Asset, AssetStatus
from app.models.transaction import Solicitacao, StatusSolicitacao
from app.models.termo_responsabilidade import TermoResponsabilidade
from app.web.dependencies import get_active_user_web
from app.core.datetime_utils import now_sp

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def require_rh_or_admin(current_user: Annotated[User, Depends(get_active_user_web)]) -> User:
    if current_user.role not in [UserRole.RH, UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso restrito ao RH e Administradores"
        )
    return current_user

DEFAULT_TEMPLATE = """TERMO DE RESPONSABILIDADE E COMPROMISSO DE USO DE EQUIPAMENTO DE TI

Pelo presente instrumento, eu, {nome_solicitante}, inscrito(a) sob a matrícula funcional nº {matricula}, ocupando o cargo de {cargo}, declaro para os devidos fins ter recebido da empresa, a título de empréstimo de uso profissional, o equipamento abaixo especificado:

• EQUIPAMENTO: {nome_ativo}
• PATRIMÔNIO / REF: {e_patrimonio}
• NÚMERO DE SÉRIE: {numero_serie}
• VALOR ESTIMADO: R$ {valor_ativo:.2f}

Mediante a assinatura deste termo, assumo o compromisso de zelar pela guarda, integridade e correta utilização do equipamento acima descrito, ciente das seguintes obrigações:

1. O equipamento destina-se exclusivamente ao uso em atividades profissionais de interesse da empresa.
2. Comprometo-me a não efetuar alterações de hardware, consertos ou desconfigurações sem a prévia autorização por escrito do departamento de TI.
3. Responsabilizo-me por qualquer dano, quebra, extravio ou perda decorrente de negligência, imperícia ou má utilização do equipamento.
4. Em caso de desligamento da empresa (por qualquer motivo), comprometo-me a devolver o equipamento imediatamente nas mesmas condições em que o recebi.

E por estar de pleno acordo com os termos acima expostos, assino o presente Termo de Responsabilidade.

São Paulo, {data_atual}.

__________________________________________________
Assinatura do Colaborador
({nome_solicitante})
"""

@router.get("/termos", response_class=HTMLResponse)
async def list_terms(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    # 1. Fetch all responsibility terms
    termos_stmt = select(TermoResponsabilidade).options(
        selectinload(TermoResponsabilidade.solicitacao),
        selectinload(TermoResponsabilidade.asset),
        selectinload(TermoResponsabilidade.usuario)
    ).order_by(TermoResponsabilidade.data_criacao.desc())
    termos = (await db.execute(termos_stmt)).scalars().all()
    
    existing_sol_ids = {t.solicitacao_id for t in termos if t.solicitacao_id is not None}
    
    # 2. Query solicitacoes approved needing a term (asset.requer_termo_rh == True)
    sols_stmt = select(Solicitacao).join(Asset).filter(
        Solicitacao.status.in_([StatusSolicitacao.APROVADA, StatusSolicitacao.ENTREGUE]),
        Asset.requer_termo_rh == True
    ).options(
        selectinload(Solicitacao.asset),
        selectinload(Solicitacao.solicitante)
    )
    sols = (await db.execute(sols_stmt)).scalars().all()
    
    # Filter out those that already have a term
    pending_sols = [s for s in sols if s.id not in existing_sol_ids]
    
    return templates.TemplateResponse("rh/termos.html", {
        "request": request,
        "user": current_user,
        "pending_sols": pending_sols,
        "termos": termos,
        "title": "Portal RH - Termos de Responsabilidade"
    })

@router.get("/termos/criar/{solicitacao_id}", response_class=HTMLResponse)
async def create_term_page(
    request: Request,
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    stmt = select(Solicitacao).options(
        selectinload(Solicitacao.asset),
        selectinload(Solicitacao.solicitante)
    ).filter(Solicitacao.id == solicitacao_id)
    res = await db.execute(stmt)
    sol = res.scalar_one_or_none()
    
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        
    # Populate the default template with solicitante/asset details
    nome_solicitante = sol.solicitante.nome if sol.solicitante else "Não informado"
    matricula = sol.solicitante.matricula if (sol.solicitante and sol.solicitante.matricula) else "N/A"
    cargo = sol.solicitante.cargo if (sol.solicitante and sol.solicitante.cargo) else "Não especificado"
    nome_ativo = sol.asset.nome if sol.asset else "Não especificado"
    e_patrimonio = sol.asset.e_patrimonio if sol.asset else "N/A"
    numero_serie = sol.asset.numero_serie if (sol.asset and sol.asset.numero_serie) else "N/A"
    valor_ativo = float(sol.asset.valor) if (sol.asset and sol.asset.valor) else 0.0
    data_atual = now_sp().strftime("%d de %B de %Y") # will be formatted in pt_BR locale if system supports it, or simple date
    
    # Simple fallback translation for months in Portuguese
    months = {
        "January": "janeiro", "February": "fevereiro", "March": "março", "April": "abril",
        "May": "maio", "June": "junho", "July": "julho", "August": "agosto",
        "September": "setembro", "October": "outubro", "November": "novembro", "December": "dezembro"
    }
    data_str = now_sp().strftime("%d de %B de %Y")
    for eng, pt in months.items():
        data_str = data_str.replace(eng, pt)
        
    conteudo_termo = DEFAULT_TEMPLATE.format(
        nome_solicitante=nome_solicitante,
        matricula=matricula,
        cargo=cargo,
        nome_ativo=nome_ativo,
        e_patrimonio=e_patrimonio,
        numero_serie=numero_serie,
        valor_ativo=valor_ativo,
        data_atual=data_str
    )
    
    return templates.TemplateResponse("rh/criar_termo.html", {
        "request": request,
        "user": current_user,
        "sol": sol,
        "conteudo_termo": conteudo_termo,
        "title": "Redigir Termo de Responsabilidade"
    })

@router.post("/termos/criar/{solicitacao_id}")
async def create_term_action(
    solicitacao_id: int,
    conteudo_termo: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    stmt = select(Solicitacao).options(selectinload(Solicitacao.asset)).filter(Solicitacao.id == solicitacao_id)
    res = await db.execute(stmt)
    sol = res.scalar_one_or_none()
    
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        
    if not sol.asset_id or not sol.solicitante_id:
        raise HTTPException(status_code=400, detail="Solicitação incompleta (sem ativo ou solicitante)")
        
    termo = TermoResponsabilidade(
        solicitacao_id=solicitacao_id,
        asset_id=sol.asset_id,
        usuario_id=sol.solicitante_id,
        conteudo_termo=conteudo_termo,
        status="Pendente"
    )
    
    db.add(termo)
    await db.commit()
    return RedirectResponse(url="/rh/termos", status_code=303)

@router.get("/termos/{termo_id}/editar", response_class=HTMLResponse)
async def edit_term_page(
    request: Request,
    termo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    stmt = select(TermoResponsabilidade).options(
        selectinload(TermoResponsabilidade.asset),
        selectinload(TermoResponsabilidade.usuario)
    ).filter(TermoResponsabilidade.id == termo_id)
    res = await db.execute(stmt)
    termo = res.scalar_one_or_none()
    
    if not termo:
        raise HTTPException(status_code=404, detail="Termo de responsabilidade não encontrado")
        
    return templates.TemplateResponse("rh/criar_termo.html", {
        "request": request,
        "user": current_user,
        "termo": termo,
        "conteudo_termo": termo.conteudo_termo,
        "title": "Editar Termo de Responsabilidade"
    })

@router.post("/termos/{termo_id}/editar")
async def edit_term_action(
    termo_id: int,
    conteudo_termo: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    stmt = select(TermoResponsabilidade).filter(TermoResponsabilidade.id == termo_id)
    res = await db.execute(stmt)
    termo = res.scalar_one_or_none()
    
    if not termo:
        raise HTTPException(status_code=404, detail="Termo de responsabilidade não encontrado")
        
    termo.conteudo_termo = conteudo_termo
    db.add(termo)
    await db.commit()
    return RedirectResponse(url="/rh/termos", status_code=303)

@router.post("/termos/{termo_id}/assinar")
async def sign_term_action(
    termo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    stmt = select(TermoResponsabilidade).filter(TermoResponsabilidade.id == termo_id)
    res = await db.execute(stmt)
    termo = res.scalar_one_or_none()
    
    if not termo:
        raise HTTPException(status_code=404, detail="Termo de responsabilidade não encontrado")
        
    termo.status = "Assinado"
    termo.data_assinatura = now_sp()
    db.add(termo)
    await db.commit()
    return RedirectResponse(url="/rh/termos", status_code=303)

@router.post("/termos/{termo_id}/cancelar")
async def cancel_term_action(
    termo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    stmt = select(TermoResponsabilidade).filter(TermoResponsabilidade.id == termo_id)
    res = await db.execute(stmt)
    termo = res.scalar_one_or_none()
    
    if not termo:
        raise HTTPException(status_code=404, detail="Termo de responsabilidade não encontrado")
        
    termo.status = "Cancelado"
    db.add(termo)
    await db.commit()
    return RedirectResponse(url="/rh/termos", status_code=303)

@router.get("/termos/{termo_id}/pdf")
async def export_term_pdf(
    request: Request,
    termo_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_rh_or_admin)]
):
    stmt = select(TermoResponsabilidade).options(
        selectinload(TermoResponsabilidade.asset),
        selectinload(TermoResponsabilidade.usuario)
    ).filter(TermoResponsabilidade.id == termo_id)
    res = await db.execute(stmt)
    termo = res.scalar_one_or_none()
    
    if not termo:
        raise HTTPException(status_code=404, detail="Termo de responsabilidade não encontrado")
        
    html_content = templates.get_template("rh/termo_pdf.html").render({
        "request": request,
        "termo": termo,
        "formatted_content": termo.conteudo_termo.replace("\n", "<br>"),
        "generated_at": now_sp().strftime("%d/%m/%Y %H:%M:%S")
    })
    
    from weasyprint import HTML
    pdf_bytes = HTML(string=html_content).write_pdf()
    
    filename = f"Termo_Responsabilidade_{termo.usuario.nome.replace(' ', '_')}_{termo.asset.e_patrimonio}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
