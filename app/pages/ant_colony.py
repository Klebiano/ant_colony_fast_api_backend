from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Literal
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import get_db
import pandas as pd
import numpy as np
import time as tm
from scripts.ant_colony import AntColony
from scripts.genetic_algorithm import GeneticAlgorithm

router = APIRouter(
    prefix="/ant-colony",
    tags=["ant-colony"],
    dependencies=[Depends(get_db)],
    responses={404: {"description": "Not found"}},
)

valid_values = Literal["Ant Colony", "Genetic", "Memetic"]

@router.get("/get-turbines-map", response_model=list[schemas.AntColonyMap])
def get_turbines_map(db: Session = Depends(get_db)):
    turbine_map_obj = crud.get_turbines_map(db)
    return turbine_map_obj


@router.get("/get-subsystems", response_model=list[schemas.Subsystems])
def get_subsystems(db: Session = Depends(get_db)):
    subsystems_obj = crud.get_subsystems(db)
    return subsystems_obj


@router.post("/run-route-optimizer", response_model=schemas.AntColonyPath)
def run_route_optmizer(turbine_faults: list[schemas.TurbineFaults], algorithm: list[valid_values] = Query(...), db: Session = Depends(get_db)):
    turbines_map = crud.get_turbines_map(db)
    downtimes = crud.get_downtimes(db)
    algorithm = algorithm[0]

    turbine_faults_df = pd.DataFrame([dict(data) for data in turbine_faults])
    turbines_map_df = pd.DataFrame([dict(data) for data in turbines_map])
    downtimes_df = pd.DataFrame([dict(data) for data in downtimes])
    downtimes_df['fault_downtime_days_norm'] = (downtimes_df['fault_downtime_days']-min(downtimes_df['fault_downtime_days']))/(max(downtimes_df['fault_downtime_days'])-min(downtimes_df['fault_downtime_days']))

    turbine_faults_df = turbine_faults_df.merge(
        turbines_map_df[['turbine_id', 'latitude', 'longitude']], on='turbine_id', how='left')

    turbine_faults_df = turbine_faults_df.merge(downtimes_df[['subsystem_name', 'fault_type', 
                                                              'anual_failure_rate', 'fault_downtime_days',
                                                              'fault_downtime_days_norm']], 
                                                              on=['subsystem_name', 'fault_type'], how='left')

    turbine_faults_df = (pd.concat([turbine_faults_df, 
                                   turbines_map_df.loc[turbines_map_df['turbine_name'] == 'Doca']])
                                    .fillna(0).sort_values(by='turbine_id'))
    
    turbine_faults_df['longitude'] = turbine_faults_df['longitude'].astype(float)
    turbine_faults_df['latitude'] = turbine_faults_df['latitude'].astype(float)

    #### Testing purposes only
    # turbine_faults_df = pd.read_csv(r'tests\\inputs\\problem_40_turbines.csv', index_col=0) 
    #### 

    turbine_faults_df[['latitude_norm', 'longitude_norm']] = turbine_faults_df[['latitude', 'longitude']].apply(lambda x: (x - x.min()) / (x.max() - x.min()))
    turbine_faults_dict = turbine_faults_df.reset_index(drop=True).to_dict('index')

    n_turbines = turbine_faults_df.shape[0] - 1
    start_run_time = tm.time()
    if (algorithm == "Ant Colony"):
        if n_turbines <= 10:
            n_ants = 3
            alpha = 5
            beta = 1.5
            rho = 0.5
        else:
            n_ants = 8
            alpha = 5
            beta = 2
            rho = 0.5

        route_optimizer = AntColony(turbine_faults_dict, 
                            n_ants=n_ants, 
                            n_iterations=200,
                            alpha=alpha, 
                            beta=beta, 
                            evaporation_rate=rho, 
                            Q=100)
        route_optimizer.ant_colony_optimization()

    else:
        if algorithm == "Genetic":
            implement_local_search = False
            if n_turbines >= 15:
                mutation_rate = 0.1
                population_size = 100
                n_generations = 50
            else:
                mutation_rate = 0.2
                population_size = 50
                n_generations = 50
        else:
            implement_local_search = True
            if n_turbines >= 40:
                mutation_rate = 0.1
                population_size = 150
                n_generations = 50
            else:
                mutation_rate = 0.2
                population_size = 50
                n_generations = 10

        route_optimizer = GeneticAlgorithm(turbine_faults_dict, 
                            population_size=population_size,
                            n_generations=n_generations,
                            mutation_rate=mutation_rate,
                            implement_local_search=implement_local_search)
        route_optimizer.evolve()

        
    end_run_time = tm.time() - start_run_time
    turbine_order = route_optimizer.turbine_order

    if turbine_order[0] == "Doca":
        turbine_order_to_show = [*turbine_order, *["Doca"]]
    elif turbine_order[-1] == "Doca":
        turbine_order_to_show = [*["Doca"], *turbine_order]
    else:
        turbine_order_to_show = [*turbine_order[turbine_order.index("Doca"):len(turbine_order) - 1], *turbine_order[:turbine_order.index("Doca")], *["Doca"]]

    route_optimzer_path_obj = {
        'turbine_order': turbine_order,
        'turbine_order_to_show': turbine_order_to_show,
        'best_path': route_optimizer.best_path,
        'best_path_length': route_optimizer.best_path_length,
        'best_downtime_days': route_optimizer.best_downtime_days,
        'best_path_len_downtime': route_optimizer.best_path_len_downtime,
        'time_to_run_sec': end_run_time,
    }
    print(route_optimzer_path_obj)
    return route_optimzer_path_obj


# @router.patch("/{asset_id}", response_model=schemas.Assets)
# def edit_asset(asset: schemas.AssetCreate, asset_id: int, db: Session = Depends(get_db)
#                ):
#     return crud.edit_assets(db=db, asset=asset, asset_id=asset_id)


# @router.delete("/{asset_id}")
# def delete_asset(asset_id: int, db: Session = Depends(get_db)):
#     result = crud.delete_asset(db, asset_id=asset_id)
#     return result
