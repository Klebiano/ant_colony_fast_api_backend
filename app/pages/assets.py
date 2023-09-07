from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/assets",
    tags=["assets"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.AssetsRead])
def read_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assets = crud.get_assets(db, skip=skip, limit=limit)
    return assets


@router.post("/", response_model=schemas.Assets)
def create_new_asset(asset: schemas.AssetCreate, db: Session = Depends(get_db)
                     ):
    return crud.create_new_asset(db=db, asset=asset)


@router.patch("/{asset_id}", response_model=schemas.Assets)
def edit_asset(asset: schemas.AssetCreate, asset_id: int, db: Session = Depends(get_db)
               ):
    return crud.edit_assets(db=db, asset=asset, asset_id=asset_id)


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    result = crud.delete_asset(db, asset_id=asset_id)
    return result
