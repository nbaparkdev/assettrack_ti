# app/web/endpoints/rh.py
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import now_sp
from app.database import get_db
from app.models.asset import Asset
from app.models.termo_responsabilidade import TermoResponsabilidade
from app.models.transaction import Solicitacao, StatusSolicitacao
from app.models.user import User, UserRole
from app.web.dependencies import get_active_user_web

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

async def require_rh_or_admin(current_user: Annotated[User, Depends(get_active_user_web)]) -> User:
    if current_user.role not in [UserRole.RH, UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso restrito ao RH e Administradores"
        )
    return current_user

DEFAULT_TEMPLATE = """TERMO DE RESPONSABILIDADE PELA GUARDA E USO DE EQUIPAMENTO

Eu, {nome_solicitante}, denominado USUÁRIO, inscrito(a) no CPF sob o nº {matricula}, declaro que recebi de NPG BRASIL PARQUES TEMÁTICOS LTDA, inscrita no CNPJ sob o nº.47.911.142/0001-74, com sede à Av. Das Hortênsias, nº 4795, Gramado/RS, a título de comodato, para uso exclusivo, os equipamentos abaixo especificados:

• EQUIPAMENTO: {nome_ativo}
• MODELO: {modelo}
• PATRIMÔNIO / REF: {e_patrimonio}
• NÚMERO DE SÉRIE: {numero_serie}


TERMOS E CONDIÇÕES
------------------

1. O equipamento deverá ser utilizado ÚNICA e EXCLUSIVAMENTE a serviço da empresa, tendo em vista a atividade a ser exercida pelo USUÁRIO;
2. Ficará o USUÁRIO responsável pelo uso e conservação do equipamento;
3. O USUÁRIO tem somente a posse do(s) item(ns) acima descrito(s), não detendo qualquer propriedade do equipamento, tendo em vista o uso exclusivo para prestação dos serviços profissionais para o qual fora contratado, sendo terminantemente proibido o empréstimo, locação e/ou cessão deste a terceiros;
4. Ao término da prestação de serviço ou do contrato individual de trabalho, o USUÁRIO compromete-se a devolver o equipamento em perfeito estado de conservação e no mesmo dia em que tiver ciência de seu desligamento, salvo o desgaste natural pelo uso natural do equipamento.
5. O USUÁRIO fica autorizado o equipamento acima descrito para sua residência, devendo seu uso ser voltado exclusivamente para fins corporativos e em viagens a trabalho, comprometendo-se a não utilizá-lo para outros fins. 
6. Na hipótese de haver roubo ou furto do equipamento, o USUÁRIO compromete-se a realizar registro de Boletim de Ocorrência junto à Autoridade Policial competente, bem como, informar a empresa de forma imediata, para que esta possa realizar o bloqueio de acesso aos dados empresariais contidos no equipamento.
7. Se o equipamento for danificado e/ou inutilizado por emprego inadequado do equipamento, mau uso, negligência, imprudência, imperícia e/ou extravio, ficará obrigado a ressarcir os prejuízos decorrentes à empresa, que cobrará o valor de 1 (um) equipamento novo da mesma marca e modelo ou similar. 

Declaro estar ciente e de acordo com as cláusulas acima.


Gramado, RS, {data_atual}.



__________________________________________________
             Assinatura Usuario




_________________________________________________
               Assinatura RH
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
    modelo = sol.asset.modelo if (sol.asset and sol.asset.modelo) else "N/A"
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
        modelo=modelo,
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
