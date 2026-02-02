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
