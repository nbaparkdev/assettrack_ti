
# app/api/v1/endpoints/assets.py
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import dependencies
from app.crud import asset as asset_crud
from app.schemas.asset import AssetCreate, AssetUpdate, AssetResponse
from app.database import get_db
from app.services.qr_service import QRService

router = APIRouter()

@router.get("/", response_model=List[AssetResponse])
async def read_assets(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    serial_number: Optional[str] = None
):
    if serial_number:
        asset = await asset_crud.asset.get_by_serial(db, serial_number=serial_number)
        return [asset] if asset else []
    return await asset_crud.asset.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_in: AssetCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    asset = await asset_crud.asset.get_by_serial(db, serial_number=asset_in.serial_number)
    if asset:
        raise HTTPException(status_code=400, detail="Asset with this serial number already exists")
        
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
    
    # Conteúdo do QR Code: pode ser a URL do frontend para visualizar o asset
    qr_content = f"assettrack://assets/{asset.id}" # ou url web
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
    
    # Supondo que o QR tenha formato "assettrack://assets/{id}"
    try:
        if "assets/" in decoded:
            asset_id = int(decoded.split("assets/")[-1])
        else:
            asset_id = int(decoded) # Tenta cast direto se for só ID

        asset = await asset_crud.asset.get(db, id=asset_id)
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset from QR not found (ID: {asset_id})")
        return asset
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid QR code content: {decoded}")
