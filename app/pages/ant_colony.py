from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
import pandas as pd
from scripts.ant_colony import AntColony

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


@router.get("/get-subsystems", response_model=list[schemas.Subsystems])
def get_subsystems(db: Session = Depends(get_db)):
    subsystems_obj = crud.get_subsystems(db)
    return subsystems_obj


@router.post("/run-ant-colony-path", response_model=list[schemas.AntColonyPath])
def run_ant_colony_path(turbine_faults: list[schemas.TurbineFaults], db: Session = Depends(get_db)):
    turbines_map = crud.get_turbines_map(db)
    downtimes = crud.get_downtimes(db)

    turbine_faults_df = pd.DataFrame([dict(data) for data in turbine_faults])
    turbines_map_df = pd.DataFrame([dict(data) for data in turbines_map])
    downtimes_df = pd.DataFrame([dict(data) for data in downtimes])

    turbine_faults_df = turbine_faults_df.merge(
        turbines_map_df[['turbine_id', 'latitude', 'longitude']], on='turbine_id', how='left')

    turbine_faults_df = turbine_faults_df.merge(downtimes_df[['subsystem_name', 'fault_type', 'anual_failure_rate', 'fault_downtime_days']], on=[
                                                'subsystem_name', 'fault_type'], how='left')

    turbine_faults_df['longitude'] = turbine_faults_df['longitude'].astype(
        float)
    turbine_faults_df['latitude'] = turbine_faults_df['latitude'].astype(float)

    return ant_colony_path_obj


# @router.patch("/{asset_id}", response_model=schemas.Assets)
# def edit_asset(asset: schemas.AssetCreate, asset_id: int, db: Session = Depends(get_db)
#                ):
#     return crud.edit_assets(db=db, asset=asset, asset_id=asset_id)


# @router.delete("/{asset_id}")
# def delete_asset(asset_id: int, db: Session = Depends(get_db)):
#     result = crud.delete_asset(db, asset_id=asset_id)
#     return result
