# app/web/endpoints/suppliers.py
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil
import logging
from datetime import datetime
import json

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.database import get_db
from app.crud import crud_supplier, crud_invoice
from app.schemas.supplier import FornecedorCreate
from app.schemas.invoice import NotaFiscalCreate

import xml.etree.ElementTree as ET

def parse_nfe_xml(file_path: str):
    """
    Extrai informações básicas de um arquivo XML de NF-e, incluindo itens.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # O XML da NF-e geralmente usa namespaces. Precisamos lidar com eles.
        ns = ""
        if '}' in root.tag:
            ns = root.tag.split('}')[0] + '}'
        
        infNFe = root.find(f".//{ns}infNFe")
        if infNFe is None:
            # Tentar encontrar sem o ponto inicial (alguns XMLs podem variar)
            infNFe = root.find(f"{ns}infNFe")
            if infNFe is None:
                return {}
            
        ide = infNFe.find(f"{ns}ide")
        emit = infNFe.find(f"{ns}emit")
        dest = infNFe.find(f"{ns}dest")
        total_node = infNFe.find(f"{ns}total/{ns}ICMSTot")
        
        # Extrair itens
        itens = []
        for det in infNFe.findall(f"{ns}det"):
            prod = det.find(f"{ns}prod")
            if prod is not None:
                item = {
                    "codigo": prod.findtext(f"{ns}cProd"),
                    "descricao": prod.findtext(f"{ns}xProd"),
                    "ncm": prod.findtext(f"{ns}NCM"),
                    "quantidade": prod.findtext(f"{ns}qCom"),
                    "valor_unitario": prod.findtext(f"{ns}vUnCom"),
                    "valor_total": prod.findtext(f"{ns}vProd")
                }
                # Tentar converter valores numéricos
                try:
                    if item["quantidade"]: item["quantidade"] = float(item["quantidade"])
                    if item["valor_unitario"]: item["valor_unitario"] = float(item["valor_unitario"])
                    if item["valor_total"]: item["valor_total"] = float(item["valor_total"])
                except:
                    pass
                itens.append(item)

        valor_total_str = total_node.findtext(f"{ns}vNF") if total_node is not None else None
        valor_total = None
        if valor_total_str:
            try:
                valor_total = float(valor_total_str)
            except:
                pass

        data = {
            "numero_nota": ide.findtext(f"{ns}nNF") if ide is not None else None,
            "data_emissao": ide.findtext(f"{ns}dhEmi") if ide is not None else None,
            "natureza_operacao": ide.findtext(f"{ns}natOp") if ide is not None else None,
            "valor_total": valor_total,
            "emitente_nome": emit.findtext(f"{ns}xNome") if emit is not None else None,
            "emitente_cnpj": emit.findtext(f"{ns}CNPJ") if emit is not None else None,
            "destinatario_nome": dest.findtext(f"{ns}xNome") if dest is not None else None,
            "destinatario_cnpj": dest.findtext(f"{ns}CNPJ") if dest is not None else None,
            "itens": itens
        }
        
        # Converter data se possível
        if data["data_emissao"]:
            try:
                # fromisoformat handles offsets like -03:00
                dt = datetime.fromisoformat(data["data_emissao"])
                data["data_emissao"] = dt.replace(tzinfo=None)
            except Exception as e:
                logger.error(f"Erro ao converter data do XML ({data['data_emissao']}): {e}")
                pass
                
        return data
    except Exception as e:
        logger.error(f"Erro ao processar XML em {file_path}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def list_suppliers(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/", status_code=303)
        
    fornecedores = await crud_supplier.get_fornecedores(db)
    return templates.TemplateResponse("suppliers/list.html", {
        "request": request,
        "user": current_user,
        "fornecedores": fornecedores,
        "title": "Fornecedores"
    })

@router.get("/new", response_class=HTMLResponse)
async def new_supplier_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/", status_code=303)
        
    return templates.TemplateResponse("suppliers/form.html", {
        "request": request,
        "user": current_user,
        "title": "Novo Fornecedor"
    })

@router.post("/new", response_class=HTMLResponse)
async def create_supplier(
    request: Request,
    nome: Annotated[str, Form()],
    razao_social: Annotated[Optional[str], Form()] = None,
    cnpj: Annotated[Optional[str], Form()] = None,
    telefone: Annotated[Optional[str], Form()] = None,
    email: Annotated[Optional[str], Form()] = None,
    endereco: Annotated[Optional[str], Form()] = None,
    cidade: Annotated[Optional[str], Form()] = None,
    estado: Annotated[Optional[str], Form()] = None,
    tipo_fornecedor: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/", status_code=303)
        
    try:
        supplier_in = FornecedorCreate(
            nome=nome,
            razao_social=razao_social,
            cnpj=cnpj,
            telefone=telefone,
            email=email,
            endereco=endereco,
            cidade=cidade,
            estado=estado,
            tipo_fornecedor=tipo_fornecedor
        )
        await crud_supplier.create_fornecedor(db, supplier_in)
        return RedirectResponse(url="/suppliers", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("suppliers/form.html", {
            "request": request,
            "user": current_user,
            "error": f"Erro ao criar fornecedor: {str(e)}",
            "title": "Novo Fornecedor"
        })

@router.get("/{fornecedor_id}/edit", response_class=HTMLResponse)
async def edit_supplier_form(
    fornecedor_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/", status_code=303)
        
    fornecedor = await crud_supplier.get_fornecedor(db, fornecedor_id)
    if not fornecedor:
        return RedirectResponse(url="/suppliers", status_code=303)
    
    # Catch error message from query params if any
    error = request.query_params.get("error")
    
    return templates.TemplateResponse("suppliers/form.html", {
        "request": request,
        "user": current_user,
        "fornecedor": fornecedor,
        "error": error,
        "title": f"Editar Fornecedor: {fornecedor.nome}"
    })

@router.post("/{fornecedor_id}/edit", response_class=HTMLResponse)
async def update_supplier(
    fornecedor_id: int,
    request: Request,
    nome: Annotated[str, Form()],
    razao_social: Annotated[Optional[str], Form()] = None,
    cnpj: Annotated[Optional[str], Form()] = None,
    telefone: Annotated[Optional[str], Form()] = None,
    email: Annotated[Optional[str], Form()] = None,
    endereco: Annotated[Optional[str], Form()] = None,
    cidade: Annotated[Optional[str], Form()] = None,
    estado: Annotated[Optional[str], Form()] = None,
    tipo_fornecedor: Annotated[Optional[str], Form()] = None,
    xml_file: Annotated[Optional[UploadFile], File()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/", status_code=303)
        
    fornecedor = await crud_supplier.get_fornecedor(db, fornecedor_id)
    if not fornecedor:
        return RedirectResponse(url="/suppliers", status_code=303)
    
    try:
        # Atualizar dados básicos
        fornecedor.nome = nome
        fornecedor.razao_social = razao_social
        fornecedor.cnpj = cnpj
        fornecedor.telefone = telefone
        fornecedor.email = email
        fornecedor.endereco = endereco
        fornecedor.cidade = cidade
        fornecedor.estado = estado
        fornecedor.tipo_fornecedor = tipo_fornecedor
        
        db.add(fornecedor)
        await db.commit()

        # Processar XML se enviado
        if xml_file and xml_file.filename:
            upload_dir = "static/uploads/xml"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{fornecedor.id}_{xml_file.filename}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(xml_file.file, buffer)
            
            # Extrair dados do XML
            xml_data = parse_nfe_xml(file_path)
            if xml_data.get("numero_nota"):
                nf_in = NotaFiscalCreate(
                    numero_nota=xml_data["numero_nota"],
                    fornecedor_id=fornecedor.id,
                    xml_path=f"/{file_path}",
                    data_emissao=xml_data.get("data_emissao"),
                    valor_total=xml_data.get("valor_total"),
                    natureza_operacao=xml_data.get("natureza_operacao"),
                    emitente_nome=xml_data.get("emitente_nome"),
                    emitente_cnpj=xml_data.get("emitente_cnpj"),
                    destinatario_nome=xml_data.get("destinatario_nome"),
                    destinatario_cnpj=xml_data.get("destinatario_cnpj"),
                    itens=xml_data.get("itens")
                )
                await crud_invoice.create_nota_fiscal(db, nf_in)
            else:
                raise ValueError("Não foi possível extrair o Número da Nota (nNF) do XML fornecido.")

        # Redirect back to the edit page so the user sees the updated list
        return RedirectResponse(url=f"/suppliers/{fornecedor_id}/edit", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("suppliers/form.html", {
            "request": request,
            "user": current_user,
            "fornecedor": fornecedor,
            "error": f"Erro ao atualizar fornecedor: {str(e)}",
            "title": f"Editar Fornecedor: {fornecedor.nome}"
        })

@router.get("/{fornecedor_id}/invoices")
async def get_supplier_invoices(
    fornecedor_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return []
        
    fornecedor = await crud_supplier.get_fornecedor(db, fornecedor_id)
    if not fornecedor:
        return []
    
    return [{"id": nf.id, "numero_nota": nf.numero_nota} for nf in fornecedor.notas_fiscais]

@router.get("/invoices/{invoice_id}")
async def get_invoice_details(
    invoice_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return {}
        
    invoice = await crud_invoice.get_nota_fiscal(db, invoice_id)
    if not invoice:
        return {}
    
    return {
        "id": invoice.id,
        "numero_nota": invoice.numero_nota,
        "data_emissao": invoice.data_emissao.strftime('%d/%m/%Y %H:%M') if invoice.data_emissao else "N/A",
        "data_emissao_iso": invoice.data_emissao.strftime('%Y-%m-%d') if invoice.data_emissao else "",
        "natureza_operacao": invoice.natureza_operacao or "N/A",
        "valor_total": float(invoice.valor_total) if invoice.valor_total else 0,
        "emitente_nome": invoice.emitente_nome or "N/A",
        "destinatario_nome": invoice.destinatario_nome or "N/A",
        "itens": invoice.itens or []
    }


@router.post("/{fornecedor_id}/invoices/{invoice_id}/delete")
async def delete_invoice(
    fornecedor_id: int,
    invoice_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url=f"/suppliers/{fornecedor_id}/edit", status_code=303)
        
    invoice = await crud_invoice.get_nota_fiscal(db, invoice_id)
    if invoice:
        # Verificar se existem ativos vinculados
        from sqlalchemy import select, func
        from app.models.asset import Asset
        asset_count = await db.scalar(select(func.count(Asset.id)).where(Asset.nota_fiscal_id == invoice_id))
        
        if asset_count > 0:
            return RedirectResponse(url=f"/suppliers/{fornecedor_id}/edit?error=Não+é+possível+excluir+nota+com+ativos+vinculados", status_code=303)

        # Deletar arquivo físico
        if invoice.xml_path:
            full_path = invoice.xml_path.lstrip('/')
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    logger.error(f"Erro ao deletar arquivo XML: {e}")

        await crud_invoice.delete_nota_fiscal(db, invoice)
        logger.info(f"User {current_user.email} deleted invoice {invoice.numero_nota} (ID: {invoice.id})")
        
    return RedirectResponse(url=f"/suppliers/{fornecedor_id}/edit", status_code=303)

@router.post("/{fornecedor_id}/delete")
async def delete_supplier(
    fornecedor_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.user import UserRole
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/suppliers", status_code=303)
        
    fornecedor = await crud_supplier.get_fornecedor(db, fornecedor_id)
    if fornecedor:
        await crud_supplier.delete_fornecedor(db, fornecedor_id)
        # Log to audit/terminal
        logger.info(f"User {current_user.email} deleted supplier {fornecedor.nome} (ID: {fornecedor.id})")
        
    return RedirectResponse(url="/suppliers", status_code=303)
