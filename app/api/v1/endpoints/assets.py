
# app/api/v1/endpoints/assets.py
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import dependencies
from app.crud import asset as asset_crud
from app.database import get_db
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.services.qr_service import QRService

router = APIRouter()

from fastapi import Request


async def get_any_active_user(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.web.dependencies import get_current_user_from_cookie
    user = await get_current_user_from_cookie(request, db=db)
    if user and user.is_active:
        return user
    
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            from jose import jwt

            from app.config import settings
            from app.crud import user as user_crud
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            email = payload.get("sub")
            if email:
                u = await user_crud.user.get_by_email(db, email=email)
                if u and u.is_active:
                    return u
        except Exception:
            pass
            
    raise HTTPException(status_code=401, detail="Não autenticado")

@router.get("/referencias")
async def get_referencias(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(get_any_active_user)]
):
    """
    Retorna tabelas de referência agregadas (categorias, setores, localizacoes, armazenamentos, fornecedores)
    otimizadas para cache de cliente (LocalStorage / IndexedDB).
    """
    from app.crud.asset_category import category as cat_crud
    from app.crud.crud_supplier import supplier as supp_crud
    from app.crud.location import armazenamento as arm_crud
    from app.crud.location import departamento as dept_crud
    from app.crud.location import localizacao as loc_crud

    cats = await cat_crud.get_multi(db, limit=500)
    depts = await dept_crud.get_multi(db, limit=500)
    locs = await loc_crud.get_multi(db, limit=500)
    arms = await arm_crud.get_multi(db, limit=500)
    supps = await supp_crud.get_multi(db, limit=500)

    return {
        "categorias": [{"id": c.id, "nome": c.nome} for c in cats],
        "setores": [{"id": d.id, "nome": d.nome} for d in depts],
        "localizacoes": [{"id": l.id, "nome": l.nome} for l in locs],
        "armazenamentos": [{"id": a.id, "nome": a.nome} for a in arms],
        "fornecedores": [{"id": s.id, "nome": getattr(s, 'nome_fantasia', None) or getattr(s, 'razao_social', f'Fornecedor {s.id}')} for s in supps]
    }

@router.get("/", response_model=list[AssetResponse])
async def read_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    e_patrimonio: str | None = None
):
    if e_patrimonio:
        asset = await asset_crud.asset.get_by_e_patrimonio(db, e_patrimonio=e_patrimonio)
        return [asset] if asset else []
    return await asset_crud.asset.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_in: AssetCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    asset = await asset_crud.asset.get_by_e_patrimonio(db, e_patrimonio=asset_in.e_patrimonio)
    if asset:
        raise HTTPException(status_code=400, detail="Asset with this E-Patrimonio already exists")
        
    created_asset = await asset_crud.asset.create(db, obj_in=asset_in)
    
    return created_asset

@router.get("/{asset_id}", response_model=AssetResponse)
async def read_asset(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_in: AssetUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return await asset_crud.asset.update(db, db_obj=asset, obj_in=asset_in)

@router.get("/{asset_id}/qrcode")
async def get_asset_qrcode(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # Conteúdo do QR Code: agora usando o E-Patrimonio para busca
    qr_content = f"assettrack://assets/ep/{asset.e_patrimonio}"
    img_io = QRService.generate_qr_code(qr_content)
    
    return Response(content=img_io.getvalue(), media_type="image/png")

@router.post("/scan-qr")
async def scan_qr_code(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    file: UploadFile = File(...)
):
    """
    Recebe um upload de imagem (arquivo) e tenta ler o QR Code
    """
    contents = await file.read()
    decoded = QRService.decode_qr_image(contents)
    
    if not decoded:
        raise HTTPException(status_code=400, detail="Could not decode QR code")
    
    # Supondo que o QR tenha formato "assettrack://assets/ep/{patrimonio}" ou "assettrack://assets/{id}"
    try:
        if "assets/ep/" in decoded:
            patrimonio = decoded.split("assets/ep/")[-1]
            asset = await asset_crud.asset.get_by_e_patrimonio(db, e_patrimonio=patrimonio)
            if not asset:
                raise HTTPException(status_code=404, detail=f"Asset with E-Patrimonio {patrimonio} not found")
            return asset
        elif "assets/sn/" in decoded:
            # Fallback for old QR codes
            serial = decoded.split("assets/sn/")[-1]
            asset = await asset_crud.asset.get_by_e_patrimonio(db, e_patrimonio=serial)
            if not asset:
                raise HTTPException(status_code=404, detail=f"Asset with former serial {serial} not found")
            return asset
        elif "assets/" in decoded:
            asset_id = int(decoded.split("assets/")[-1])
            asset = await asset_crud.asset.get(db, id=asset_id)
        else:
            # Tenta ID direto como fallback
            asset_id = int(decoded)
            asset = await asset_crud.asset.get(db, id=asset_id)

        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        return asset
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid QR code content: {decoded}")
