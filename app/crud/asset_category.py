from app.crud.base import CRUDBase
from app.models.asset_category import AssetCategory
from app.schemas.asset_category import AssetCategoryCreate, AssetCategoryUpdate


class CRUDAssetCategory(CRUDBase[AssetCategory, AssetCategoryCreate, AssetCategoryUpdate]):
    pass


category = CRUDAssetCategory(AssetCategory)
