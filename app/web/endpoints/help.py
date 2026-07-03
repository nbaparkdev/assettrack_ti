from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/help", include_in_schema=False)
async def help_page(
    request: Request,
    current_user: User = Depends(get_active_user_web)
):
    """
    Renderiza a página de ajuda baseada no perfil do usuário.
    """
    # Se for usuario comum, renderiza help/user.html (Manual Reduzido)
    if current_user.role == UserRole.USUARIO:
        return templates.TemplateResponse(
            "help/user.html", 
            {"request": request, "user": current_user, "title": "Ajuda"}
        )
    
    # Se for Admin, Gerente ou Técnico, renderiza help/admin.html (Manual Completo)
    return templates.TemplateResponse(
        "help/admin.html", 
        {"request": request, "user": current_user, "title": "Manual do Sistema"}
    )

@router.get("/help/export", include_in_schema=False)
async def export_help_pdf(
    request: Request,
    current_user: User = Depends(get_active_user_web)
):
    from weasyprint import HTML
    from app.core.datetime_utils import now_sp
    from fastapi.responses import Response

    html_content = templates.get_template("help/pdf.html").render({
        "request": request,
        "user": current_user,
        "generated_at": now_sp().strftime("%d/%m/%Y %H:%M")
    })

    pdf_bytes = HTML(string=html_content).write_pdf()

    filename = f"Manual_AssetTrack_{now_sp().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

