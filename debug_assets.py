import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.crud import asset as asset_crud

async def check_assets():
    async with SessionLocal() as db:
        assets = await asset_crud.asset.get_multi(db)
        print(f"Found {len(assets)} assets.")
        for asset in assets:
            print(f"ID: {asset.id}, Status: {asset.status!r}, Type: {type(asset.status)}")
            if hasattr(asset.status, 'value'):
                print(f"  Has .value: {asset.status.value}")
            else:
                print("  NO .value attribute!")

if __name__ == "__main__":
    asyncio.run(check_assets())
