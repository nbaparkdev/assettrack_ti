# app/web/endpoints/avisos.py
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from urllib.parse import quote_plus

from app.database import get_db
from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.aviso import Aviso
from app.crud.aviso import aviso as aviso_crud

router = APIRouter(prefix="/admin/avisos", tags=["admin-avisos"])
templates = Jinja2Templates(directory="app/templates")

async def require_admin(current_user: Annotated[User, Depends(get_active_user_web)]):
    """Verifica se o usuário é Administrador ou Gerente"""
    if str(current_user.role.value).lower() not in ["admin", "gerente_ti", "gerente_infra"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return current_user

def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str or not date_str.strip():
        return None
    try:
        # datetime-local input sends 'YYYY-MM-DDTHH:MM'
        return datetime.fromisoformat(date_str)
    except ValueError:
        return None

@router.get("", response_class=HTMLResponse)
async def list_avisos(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    error: Optional[str] = None,
    success: Optional[str] = None
):
    """Lista todos os avisos criados para o administrador gerenciar"""
    result = await db.execute(select(Aviso).order_by(Aviso.data_cadastro.desc()))
    avisos = result.scalars().all()
    
    return templates.TemplateResponse("admin/avisos.html", {
        "request": request,
        "user": admin,
        "avisos": avisos,
        "error": error,
        "success": success,
        "title": "Gerenciar Avisos"
    })

@router.post("/new")
async def create_aviso(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    titulo: str = Form(...),
    texto: str = Form(None),
    midia_url: str = Form(None),
    midia_tipo: str = Form(None),
    link_url: str = Form(None),
    link_texto: str = Form(None),
    programado_inicio: str = Form(None),
    programado_fim: str = Form(None),
    ativo: bool = Form(False)
):
    """Cria um novo aviso"""
    from app.core.errors import get_friendly_db_error
    try:
        # Tratamento de campos de mídia
        m_tipo = midia_tipo if midia_tipo in ["imagem", "video"] else None
        m_url = midia_url.strip() if midia_url and midia_url.strip() else None
        
        inicio = parse_date(programado_inicio)
        fim = parse_date(programado_fim)
        
        new_aviso = Aviso(
            titulo=titulo.strip(),
            texto=texto.strip() if texto else None,
            midia_url=m_url,
            midia_tipo=m_tipo if m_url else None,
            link_url=link_url.strip() if link_url else None,
            link_texto=link_texto.strip() if link_texto else None,
            ativo=ativo,
            programado_inicio=inicio,
            programado_fim=fim
        )
        db.add(new_aviso)
        await db.commit()
        
        return RedirectResponse(url="/admin/avisos?success=Aviso+criado+com+sucesso", status_code=303)
    except Exception as e:
        await db.rollback()
        friendly_error = get_friendly_db_error(e)
        return RedirectResponse(url=f"/admin/avisos?error={quote_plus(friendly_error)}", status_code=303)

@router.post("/{aviso_id}/edit")
async def edit_aviso(
    aviso_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    titulo: str = Form(...),
    texto: str = Form(None),
    midia_url: str = Form(None),
    midia_tipo: str = Form(None),
    link_url: str = Form(None),
    link_texto: str = Form(None),
    programado_inicio: str = Form(None),
    programado_fim: str = Form(None),
    ativo: bool = Form(False)
):
    """Edita um aviso existente"""
    from app.core.errors import get_friendly_db_error
    aviso_obj = await db.get(Aviso, aviso_id)
    if not aviso_obj:
        raise HTTPException(status_code=404, detail="Aviso não encontrado")
        
    try:
        m_tipo = midia_tipo if midia_tipo in ["imagem", "video"] else None
        m_url = midia_url.strip() if midia_url and midia_url.strip() else None
        
        aviso_obj.titulo = titulo.strip()
        aviso_obj.texto = texto.strip() if texto else None
        aviso_obj.midia_url = m_url
        aviso_obj.midia_tipo = m_tipo if m_url else None
        aviso_obj.link_url = link_url.strip() if link_url else None
        aviso_obj.link_texto = link_texto.strip() if link_texto else None
        aviso_obj.ativo = ativo
        aviso_obj.programado_inicio = parse_date(programado_inicio)
        aviso_obj.programado_fim = parse_date(programado_fim)
        
        await db.commit()
        return RedirectResponse(url="/admin/avisos?success=Aviso+atualizado+com+sucesso", status_code=303)
    except Exception as e:
        await db.rollback()
        friendly_error = get_friendly_db_error(e)
        return RedirectResponse(url=f"/admin/avisos?error={quote_plus(friendly_error)}", status_code=303)

@router.post("/{aviso_id}/toggle")
async def toggle_aviso(
    aviso_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Ativa ou desativa instantaneamente um aviso (Aplica e retira em tempo real)"""
    aviso_obj = await db.get(Aviso, aviso_id)
    if not aviso_obj:
        return JSONResponse(status_code=404, content={"detail": "Aviso não encontrado"})
        
    aviso_obj.ativo = not aviso_obj.ativo
    await db.commit()
    
    return JSONResponse(content={
        "status": "success",
        "ativo": aviso_obj.ativo,
        "message": f"Aviso {'ativado' if aviso_obj.ativo else 'desativado'} com sucesso."
    })

@router.post("/{aviso_id}/delete")
async def delete_aviso(
    aviso_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Exclui um aviso"""
    aviso_obj = await db.get(Aviso, aviso_id)
    if not aviso_obj:
         raise HTTPException(status_code=404, detail="Aviso não encontrado")
         
    await db.delete(aviso_obj)
    await db.commit()
    return RedirectResponse(url="/admin/avisos?success=Aviso+excluído+com+sucesso", status_code=303)

# Rota pública para retornar avisos ativos em tempo real (JSON)
# Acessível via AJAX no dashboard dos usuários
@router.get("/active-list")
async def get_active_avisos_api(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Retorna os avisos ativos para exibição em tempo real na Home/Dashboard"""
    active_avisos = await aviso_crud.get_active_announcements(db)
    
    # Serializa os objetos SQLAlchemy para JSON seguro
    data = []
    for a in active_avisos:
        data.append({
            "id": a.id,
            "titulo": a.titulo,
            "texto": a.texto,
            "midia_url": a.midia_url,
            "midia_tipo": a.midia_tipo,
            "link_url": a.link_url,
            "link_texto": a.link_texto or "Ver Detalhes"
        })
    return JSONResponse(content={"avisos": data})
