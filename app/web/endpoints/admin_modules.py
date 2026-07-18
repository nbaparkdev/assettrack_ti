# app/web/endpoints/admin_modules.py
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.web.dependencies import get_admin_user_web
from app.models.user import User
from app.crud.system_settings import system_settings

router = APIRouter(dependencies=[Depends(get_admin_user_web)])
templates = Jinja2Templates(directory="app/templates")

@router.get("/modulos", response_class=HTMLResponse)
async def gerenciar_modulos_page(
    request: Request,
    current_user: Annotated[User, Depends(get_admin_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Página para gerenciar a ativação/desativação de módulos do sistema e permissões de menus"""
    pm_enabled_str = await system_settings.get_setting(db, "preventive_maintenance_enabled", default_value="true")
    pm_enabled = pm_enabled_str.lower() == "true"
    
    purchases_enabled_str = await system_settings.get_setting(db, "purchases_enabled", default_value="true")
    purchases_enabled = purchases_enabled_str.lower() == "true"
    
    ai_enabled_str = await system_settings.get_setting(db, "ai_enabled", default_value="false")
    ai_enabled = ai_enabled_str.lower() == "true"
    
    ai_advanced_str = await system_settings.get_setting(db, "ai_advanced_functions", default_value="false")
    ai_advanced_functions = ai_advanced_str.lower() == "true"
    
    ai_provider = await system_settings.get_setting(db, "ai_provider", default_value="openai")
    openai_api_key = await system_settings.get_setting(db, "openai_api_key", default_value="")
    gemini_api_key = await system_settings.get_setting(db, "gemini_api_key", default_value="")
    groq_api_key = await system_settings.get_setting(db, "groq_api_key", default_value="")
    openai_model = await system_settings.get_setting(db, "openai_model", default_value="gpt-4o-mini")
    gemini_model = await system_settings.get_setting(db, "gemini_model", default_value="gemini-2.5-flash")
    groq_model = await system_settings.get_setting(db, "groq_model", default_value="llama-3.1-8b-instant")
    openrouter_api_key = await system_settings.get_setting(db, "openrouter_api_key", default_value="")
    kimi_api_key = await system_settings.get_setting(db, "kimi_api_key", default_value="")
    openrouter_model = await system_settings.get_setting(db, "openrouter_model", default_value="meta-llama/llama-3.1-8b-instruct:free")
    kimi_model = await system_settings.get_setting(db, "kimi_model", default_value="kimi-k2.6")
    
    # SMTP Configs (chave padronizada: smtp_password)
    smtp_host = await system_settings.get_setting(db, "smtp_host", default_value="")
    smtp_port = await system_settings.get_setting(db, "smtp_port", default_value="587")
    smtp_user = await system_settings.get_setting(db, "smtp_user", default_value="")
    smtp_pass = await system_settings.get_setting(db, "smtp_password", default_value="")
    smtp_from = await system_settings.get_setting(db, "smtp_from", default_value="")
    smtp_tls = await system_settings.get_setting(db, "smtp_tls", default_value="true")
    
    # Custom Links Comum
    custom_links_comum = await system_settings.get_setting(db, "custom_links_comum", default_value="")
    
    # Carregar permissões de menu
    import json
    perms_str = await system_settings.get_setting(db, "menu_permissions")
    if perms_str:
        try:
            menu_permissions = json.loads(perms_str)
        except Exception:
            menu_permissions = {}
    else:
        menu_permissions = {}
        
    # Valores padrão de permissões
    default_permissions = {
        "ativos": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
        "fornecedores": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "manutencao": ["admin", "gerente_ti", "gerente_infra", "tecnico"],
        "tickets": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
        "compras": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "relatorios": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "usuarios": ["admin", "gerente_ti", "gerente_infra"],
        "backup": ["admin", "gerente_ti", "gerente_infra"]
    }
    for k, v in default_permissions.items():
        if k not in menu_permissions:
            menu_permissions[k] = v

    success = request.query_params.get("success") == "1"

    # Definir listas de perfis e menus para a matriz
    roles = [
        {"value": "admin", "label": "Administrador"},
        {"value": "gerente_ti", "label": "Gerente TI"},
        {"value": "gerente_infra", "label": "Gerente Infra"},
        {"value": "tecnico", "label": "Técnico"},
        {"value": "comprador", "label": "Comprador"},
        {"value": "usuario_comum", "label": "Usuário Comum"}
    ]
    
    menus = [
        {"key": "ativos", "label": "Ativos & Patrimônio"},
        {"key": "fornecedores", "label": "Fornecedores"},
        {"key": "manutencao", "label": "Manutenção Preventiva"},
        {"key": "tickets", "label": "Service Desk / Tickets"},
        {"key": "compras", "label": "Compras & Almoxarifado"},
        {"key": "relatorios", "label": "Relatórios"},
        {"key": "usuarios", "label": "Gerenciar Usuários (Admin)"},
        {"key": "backup", "label": "Backup do Sistema (Admin)"}
    ]

    return templates.TemplateResponse("admin/modules.html", {
        "request": request,
        "user": current_user,
        "pm_enabled": pm_enabled,
        "purchases_enabled": purchases_enabled,
        "ai_enabled": ai_enabled,
        "ai_advanced_functions": ai_advanced_functions,
        "ai_provider": ai_provider,
        "openai_api_key": openai_api_key,
        "gemini_api_key": gemini_api_key,
        "groq_api_key": groq_api_key,
        "openrouter_api_key": openrouter_api_key,
        "kimi_api_key": kimi_api_key,
        "openai_model": openai_model,
        "gemini_model": gemini_model,
        "groq_model": groq_model,
        "openrouter_model": openrouter_model,
        "kimi_model": kimi_model,
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_pass": smtp_pass,
        "smtp_from": smtp_from,
        "smtp_tls": smtp_tls,
        "menu_permissions": menu_permissions,
        "roles": roles,
        "menus": menus,
        "custom_links_comum": custom_links_comum,
        "success": success,
        "title": "Gerenciar Módulos e Acessos"
    })

@router.post("/modulos")
async def gerenciar_modulos_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_admin_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    preventive_maintenance_enabled: Optional[str] = Form(None),
    purchases_enabled: Optional[str] = Form(None),
    ai_enabled: Optional[str] = Form(None),
    ai_advanced_functions: Optional[str] = Form(None),
    ai_provider: Optional[str] = Form(None),
    openai_api_key: Optional[str] = Form(None),
    gemini_api_key: Optional[str] = Form(None),
    groq_api_key: Optional[str] = Form(None),
    openai_model: Optional[str] = Form(None),
    gemini_model: Optional[str] = Form(None),
    groq_model: Optional[str] = Form(None),
    openrouter_api_key: Optional[str] = Form(None),
    openrouter_model: Optional[str] = Form(None),
    kimi_api_key: Optional[str] = Form(None),
    kimi_model: Optional[str] = Form(None),
    smtp_host: Optional[str] = Form(None),
    smtp_port: Optional[str] = Form(None),
    smtp_user: Optional[str] = Form(None),
    smtp_pass: Optional[str] = Form(None),
    smtp_from: Optional[str] = Form(None),
    smtp_tls: Optional[str] = Form(None),
    custom_links_comum: Optional[str] = Form(None)
):
    # Salvar módulos
    enabled_val = "true" if preventive_maintenance_enabled == "on" else "false"
    await system_settings.set_setting(
        db=db,
        setting_key="preventive_maintenance_enabled",
        setting_value=enabled_val,
        descricao="Ativação do módulo de Manutenção Preventiva e Corretiva"
    )
    request.app.state.pm_enabled = (enabled_val == "true")

    pur_enabled_val = "true" if purchases_enabled == "on" else "false"
    await system_settings.set_setting(
        db=db,
        setting_key="purchases_enabled",
        setting_value=pur_enabled_val,
        descricao="Ativação do módulo de Compras (Procurement)"
    )
    request.app.state.purchases_enabled = (pur_enabled_val == "true")

    ai_enabled_val = "true" if ai_enabled == "on" else "false"
    await system_settings.set_setting(
        db=db,
        setting_key="ai_enabled",
        setting_value=ai_enabled_val,
        descricao="Ativação do Assistente de IA"
    )
    request.app.state.ai_enabled = (ai_enabled_val == "true")

    ai_adv_val = "true" if ai_advanced_functions == "on" else "false"
    await system_settings.set_setting(
        db=db,
        setting_key="ai_advanced_functions",
        setting_value=ai_adv_val,
        descricao="Permitir Ações Avançadas da IA (Criar/Modificar)"
    )
    request.app.state.ai_advanced_functions = (ai_adv_val == "true")

    if ai_provider:
        await system_settings.set_setting(db=db, setting_key="ai_provider", setting_value=ai_provider, descricao="Provedor do Assistente de IA")
    if openai_api_key is not None:
        await system_settings.set_setting(db=db, setting_key="openai_api_key", setting_value=openai_api_key, descricao="Chave de API OpenAI")
    if gemini_api_key is not None:
        await system_settings.set_setting(db=db, setting_key="gemini_api_key", setting_value=gemini_api_key, descricao="Chave de API Gemini")
    if groq_api_key is not None:
        await system_settings.set_setting(db=db, setting_key="groq_api_key", setting_value=groq_api_key, descricao="Chave de API Groq")
    if openai_model:
        await system_settings.set_setting(db=db, setting_key="openai_model", setting_value=openai_model, descricao="Modelo OpenAI")
    if gemini_model:
        await system_settings.set_setting(db=db, setting_key="gemini_model", setting_value=gemini_model, descricao="Modelo Gemini")
    if groq_model:
        await system_settings.set_setting(db=db, setting_key="groq_model", setting_value=groq_model, descricao="Modelo Groq")
    if openrouter_api_key is not None:
        await system_settings.set_setting(db=db, setting_key="openrouter_api_key", setting_value=openrouter_api_key, descricao="Chave de API OpenRouter")
    if kimi_api_key is not None:
        await system_settings.set_setting(db=db, setting_key="kimi_api_key", setting_value=kimi_api_key, descricao="Chave de API Kimi")
    if openrouter_model:
        await system_settings.set_setting(db=db, setting_key="openrouter_model", setting_value=openrouter_model, descricao="Modelo OpenRouter")
    if kimi_model:
        await system_settings.set_setting(db=db, setting_key="kimi_model", setting_value=kimi_model, descricao="Modelo Kimi")

    # Salvar configurações SMTP (chave padronizada: smtp_password)
    await system_settings.set_setting(db=db, setting_key="smtp_host", setting_value=smtp_host or "")
    await system_settings.set_setting(db=db, setting_key="smtp_port", setting_value=smtp_port or "587")
    await system_settings.set_setting(db=db, setting_key="smtp_user", setting_value=smtp_user or "")
    # Salva sempre, mesmo se vazio, para manter consistência
    await system_settings.set_setting(db=db, setting_key="smtp_password", setting_value=smtp_pass or "")
    await system_settings.set_setting(db=db, setting_key="smtp_from", setting_value=smtp_from or "")
    await system_settings.set_setting(db=db, setting_key="smtp_tls", setting_value="true" if smtp_tls == "on" else "false")
    
    # Custom Links
    await system_settings.set_setting(db=db, setting_key="custom_links_comum", setting_value=custom_links_comum or "")

    # Processar permissões do menu
    form_data = await request.form()
    menus = ["ativos", "fornecedores", "manutencao", "tickets", "compras", "relatorios", "usuarios", "backup"]
    
    new_permissions = {m: [] for m in menus}
    for key, val in form_data.items():
        if key.startswith("menu_"):
            parts = key.split("_", 2)
            if len(parts) >= 3:
                menu_key = parts[1]
                role_value = parts[2]
                if menu_key in new_permissions:
                    new_permissions[menu_key].append(role_value)
                    
    # Sempre garantir que o admin tenha acesso a tudo para evitar lock-out acidental
    for m in menus:
        if "admin" not in new_permissions[m]:
            new_permissions[m].append("admin")

    import json
    perms_str = json.dumps(new_permissions)
    try:
        await system_settings.set_setting(
            db=db,
            setting_key="menu_permissions",
            setting_value=perms_str,
            descricao="Mapeamento de permissões de acesso por menu e perfil"
        )
        await db.commit()
    except Exception:
        await db.rollback()
        
    request.app.state.menu_permissions = new_permissions

    return RedirectResponse(url="/admin/modulos?success=1", status_code=status.HTTP_303_SEE_OTHER)

from pydantic import BaseModel
import smtplib
from email.message import EmailMessage

class SmtpTestRequest(BaseModel):
    email: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    smtp_from: str
    smtp_tls: bool

@router.post("/smtp/test")
async def test_smtp_connection(
    req: SmtpTestRequest,
    current_user: Annotated[User, Depends(get_admin_user_web)]
):
    from fastapi import HTTPException
    import asyncio

    # Validação antecipada para retornar mensagem clara ao usuário
    if not req.smtp_host:
        raise HTTPException(status_code=400, detail="Servidor SMTP não configurado. Preencha o campo 'Servidor SMTP' e salve antes de testar.")
    if not req.smtp_user:
        raise HTTPException(status_code=400, detail="Usuário SMTP não configurado. Preencha o campo 'Usuário SMTP' e salve antes de testar.")
    if not req.smtp_pass:
        raise HTTPException(status_code=400, detail="Senha SMTP não configurada. Preencha o campo 'Senha SMTP', salve as configurações e tente novamente.")
    if not req.email:
        raise HTTPException(status_code=400, detail="Informe um e-mail de destino para o teste.")

    try:
        msg = EmailMessage()
        msg.set_content(
            f"Este é um e-mail de teste do ERP AssetTrack TI disparado por {current_user.nome}.\n"
            f"Se você recebeu, as configurações SMTP estão corretas!"
        )
        msg["Subject"] = "[AssetTrack TI] Teste de Configuração SMTP"
        msg["From"] = req.smtp_from or req.smtp_user
        msg["To"] = req.email

        # Executa em thread para não bloquear o event loop
        def _send():
            server = smtplib.SMTP(req.smtp_host, req.smtp_port, timeout=15)
            if req.smtp_tls:
                server.ehlo()
                server.starttls()
                server.ehlo()
            server.login(req.smtp_user, req.smtp_pass)
            server.send_message(msg)
            server.quit()

        await asyncio.to_thread(_send)
        return {"message": f"E-mail enviado com sucesso para {req.email}! Verifique sua caixa de entrada."}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=400, detail="Erro de autenticação SMTP: usuário ou senha incorretos. Para Gmail, use uma 'Senha de App' em vez da senha principal.")
    except smtplib.SMTPConnectError as e:
        raise HTTPException(status_code=400, detail=f"Falha ao conectar ao servidor SMTP ({req.smtp_host}:{req.smtp_port}). Verifique o host e a porta.")
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=400, detail=f"Erro SMTP: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro inesperado: {str(e)}")
