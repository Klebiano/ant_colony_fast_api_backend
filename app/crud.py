from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from . import models, schemas

import requests
import json


def get_turbines_map(db: Session):
    query_str = text('''SELECT 
                            map."TURBINE_ID" as turbine_id,
                            map."TURBINE_NAME" as turbine_name,
                            map."LATITUDE" as latitude,
                            map."LONGITUDE" as longitude
                            -- map."LATITUDE_NORM",
                            -- map."LONGITUDE_NORM"
                        FROM 
                            wind_farm_map_points map''')

    response = db.execute(query_str).all()
    return response


def get_subsystems(db: Session):
    query_str = text('''SELECT 
                            sub."SUBSYSTEM_ID" as subsystem_id,
                            sub."SUBSYSTEM_NAME" as subsystem_name
                        FROM 
                            subsystem sub''')

    response = db.execute(query_str).all()
    return response


def get_downtimes(db: Session):
    query_str = text('''SELECT 
                            sub."SUBSYSTEM_ID" as subsystem_id,
                            sub."SUBSYSTEM_NAME" as subsystem_name,
                            dwt."FAULT_TYPE" as fault_type,
                            dwt."ANUAL_FAILURE_RATE" as anual_failure_rate,
                            dwt."FAULT_DOWNTIME_DAYS" as fault_downtime_days
                        FROM 
                            subsystem sub
                            LEFT JOIN downtime as dwt on sub."SUBSYSTEM_ID" = dwt."SUBSYSTEM_ID"
                        ''')

    response = db.execute(query_str).all()
    return response

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_wallets(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Wallet).filter(models.User.id == user_id).offset(skip).limit(limit).all()


def create_user_wallet(db: Session, wallet: schemas.WalletCreate, user_id: int):
    db_wallet = models.Wallet(**wallet.dict(), owner_id=user_id)
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet

def create_new_asset(db: Session, asset: schemas.AssetCreate):
    db_asset = models.Asset(**asset.dict())
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset

def delete_user_wallet(db: Session, wallet_id: schemas.WalletCreate, user_id: int):
    db_wallet = db.query(models.Wallet)\
        .filter((models.Wallet.id == wallet_id) and (models.Wallet.owner_id == user_id)).first()

    if not db_wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    db.delete(db_wallet)
    db.commit()
    return {'deleted': True}


def get_currency(currency):
    get_test_url= f"https://economia.awesomeapi.com.br/json/last/{currency}"

    response = requests.get(get_test_url)
    if response.status_code == 200:
        return json.loads(response.content.decode('utf-8'))
    else:
        return 'No data'


def get_assets(db: Session, skip: int = 0, limit: int = 100):
    # response = db.query(models.Asset).offset(skip).limit(limit).all()
    query = text('''SELECT  
                asset.asset_id,
                asset.asset_name,
                asset.asset_ticker,
                asset.asset_type_id,
                asset_types.currency_unit,
                asset_types.asset_type_name
            FROM asset as asset 
            LEFT JOIN asset_types as asset_types on asset.asset_type_id = asset_types.asset_type_id
            LIMIT :limit
            OFFSET :offset ''')
    params = {
        'limit': limit,
        'offset': skip
    }
    response = db.execute(
            query,
            params).all()
    return response

def edit_assets(db: Session, asset: schemas.AssetsUpdate, asset_id: int):
    db_asset = db.query(models.Asset).filter(models.Asset.id == asset_id).first()

    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset_data = asset.dict(exclude_unset=True)
    for key, value in asset_data.items():
        setattr(db_asset, key, value)
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    return db_asset


def delete_asset(db: Session, asset_id: int):
    db_asset = db.query(models.Asset).filter(models.Asset.asset_id == asset_id).first()

    if not db_asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(db_asset)
    db.commit()
    return {'deleted': True}


def get_transactions(db: Session, skip: int = 0, limit: int = 1000):
    return db.query(models.Transactions).offset(skip).limit(limit).all()
