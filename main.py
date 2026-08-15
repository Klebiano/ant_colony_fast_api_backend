from unittest import result
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, FastAPI, HTTPException
from app.pages import assets, transactions, ant_colony
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:4173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.post("/users/", response_model=schemas.User)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     db_user = crud.get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return crud.create_user(db=db, user=user)


# @app.get("/users/", response_model=list[schemas.User])
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = crud.get_users(db, skip=skip, limit=limit)
#     return users


# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(user_id: int, db: Session = Depends(get_db)):
#     db_user = crud.get_user(db, user_id=user_id)
#     if db_user is None:
#         raise HTTPException(status_code=404, detail="User not found")
#     return db_user


# @app.post("/users/{user_id}/wallets/", response_model=schemas.Wallet)
# def create_wallet_for_user(
#     user_id: int, wallet: schemas.WalletCreate, db: Session = Depends(get_db)
# ):
#     return crud.create_user_wallet(db=db, wallet=wallet, user_id=user_id)


# @app.get("/users/{user_id}/wallets/", response_model=list[schemas.Wallet])
# def read_wallets(user_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     wallets = crud.get_wallets(db, skip=skip, limit=limit, user_id=user_id)
#     return wallets


# @app.delete("/users/{user_id}/wallets/{wallet_id}")
# def delete_wallet(user_id: int, wallet_id: int, db: Session = Depends(get_db)):
#     result = crud.delete_user_wallet(db, wallet_id=wallet_id, user_id=user_id)
#     return result


# @app.get('/get-currency/{currency}')
# def get_currency(currency: str):
#     result = crud.get_currency(currency)
#     return result


# app.include_router(assets.router)
# app.include_router(transactions.router)
app.include_router(ant_colony.router)