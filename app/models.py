from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float
from sqlalchemy.orm import relationship

from .database import Base


# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True)
#     hashed_password = Column(String)
#     is_active = Column(Boolean, default=True)

#     wallets = relationship("Wallet", back_populates="owner")


# class Wallet(Base):
#     __tablename__ = "wallets"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String, index=True)
#     owner_id = Column(Integer, ForeignKey("users.id"))

#     owner = relationship("User", back_populates="wallets")


# class Transactions(Base):
#     __tablename__ = "transactions"

#     id = Column(Integer, primary_key=True, index=True)
#     wallet_id = Column(Integer, ForeignKey("wallets.id"))
#     asset_id = Column(Integer, ForeignKey("assets.id"))
#     order_type = Column(String)
#     date = Column(Date)
#     quantity = Column(Float)
#     price = Column(Float)

#     asset = relationship('Asset')
#     wallet = relationship('Wallet')


# class Asset(Base):
#     __tablename__ = "asset"

#     asset_id = Column(Integer, primary_key=True, index=True)
#     asset_name = Column(String, unique=True, index=True)
#     asset_type_id = Column(Integer)
#     asset_ticker = Column(String, unique=True, index=True)

    # asset_types = relationship('AssetTypes')

# class AssetTypes(Base):
#     __tablename__ = "asset_types"

#     asset_type_id = Column(Integer, primary_key=True, index=True)
#     asset_type_name = Column(String, unique=True, index=True)
#     currency_unit = Column(String)

# class WindfarmMapPoints(Base):
#     __tablename__ = "wind_farm_map_points"

#     turbine_id = Column(Integer, primary_key=True, index=True)
#     turbine_name = Column(String)
#     latitude = Column(Float)
#     longitude = Column(Float)