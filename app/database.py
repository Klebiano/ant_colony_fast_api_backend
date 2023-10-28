from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import urllib
from pathlib import Path

dotenv_path = Path(r'C:\Users\klebi\OneDrive\Documentos\TCC\offshore_ant_web_dev\backend\.env')
load_dotenv(dotenv_path=dotenv_path)

DB_user = os.getenv('DB_user')
DB_password = os.getenv('DB_password')
DB_name = os.getenv('DB_name')

# SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_user}:{urllib.parse.quote_plus(DB_password)}@localhost/{DB_name}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_timeout=120
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
