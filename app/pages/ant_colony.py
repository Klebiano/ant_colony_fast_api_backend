from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/ant-colony",
    tags=["ant-colony"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)


@router.get("/get-turbines-map", response_model=list[schemas.AntColonyMap])
def get_turbines_map(db: Session = Depends(get_db)):
    turbine_map_obj = crud.get_turbines_map(db)
    return turbine_map_obj


# @router.post("/", response_model=schemas.Assets)
# def create_new_asset(asset: schemas.AssetCreate, db: Session = Depends(get_db)
#                      ):
#     return crud.create_new_asset(db=db, asset=asset)


# @router.patch("/{asset_id}", response_model=schemas.Assets)
# def edit_asset(asset: schemas.AssetCreate, asset_id: int, db: Session = Depends(get_db)
#                ):
#     return crud.edit_assets(db=db, asset=asset, asset_id=asset_id)


# @router.delete("/{asset_id}")
# def delete_asset(asset_id: int, db: Session = Depends(get_db)):
#     result = crud.delete_asset(db, asset_id=asset_id)
#     return result
