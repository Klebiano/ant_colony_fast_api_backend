from pydantic import BaseModel, Field
from typing import List, Optional
# from sqlmodel import SQLModel, Relationship
from datetime import date


class WalletBase(BaseModel):
    title: str
    description: str | None = None


class AssetBase(BaseModel):
    asset_id: int = Field(default=None, primary_key=True)
    asset_name: str
    asset_type_id: int
    asset_ticker: str


class AssetTypesBase(BaseModel):
    asset_type_id: int = Field(default=None, primary_key=True)
    asset_type_name: str
    currency_unit: str


class WalletCreate(WalletBase):
    pass


class AssetCreate(AssetBase):
    pass


class Wallet(WalletBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    wallets: list[Wallet] = []

    class Config:
        orm_mode = True


class Assets(AssetBase):
    asset_id: int
    asset_name: str
    asset_ticker: str
    currency_unit: str
    asset_type_name: str


    class Config:
        orm_mode = True


class AssetsRead(AssetBase, AssetTypesBase):
    class Config:
        orm_mode = True


class AssetsUpdate(AssetBase):
    name: str
    ticker: str
    unit: str
    type: str


class TransactionsBase(BaseModel):
    id: int
    order_type: str
    date: date
    quantity: float
    price: float

    wallet: Wallet = None
    asset: Assets = None

    class Config:
        orm_mode = True


class Transactions(TransactionsBase):
    pass


class AntColonyMap(BaseModel):
    turbine_id: int
    turbine_name: str
    latitude: float
    longitude: float


class GeoPath(BaseModel):
    latitude: float
    longitude: float


class Subsystems(BaseModel):
    subsystem_id: int
    subsystem_name: str


class TurbineFaults(BaseModel):
    turbine_id: int
    turbine_name: str
    subsystem_name: str
    fault_type: str


class AntColonyPath(BaseModel):
    turbine_id: int
    path: list[GeoPath] = []
