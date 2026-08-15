from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import urllib
from pathlib import Path

dotenv_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

DB_user = os.getenv('DB_user', 'postgres')
DB_password = os.getenv('DB_password', '')
DB_name = os.getenv('DB_name', 'wind_maintenance')
DB_engine_type = os.getenv('DB_ENGINE', '').lower()

def get_engine():
    if DB_engine_type == 'sqlite':
        return create_engine("sqlite:///./sql_app.db", connect_args={"check_same_thread": False})
    
    encoded_password = urllib.parse.quote_plus(DB_password) if DB_password else ""
    pg_url = f"postgresql+psycopg2://{DB_user}:{encoded_password}@localhost/{DB_name}"
    try:
        eng = create_engine(pg_url, pool_size=20, max_overflow=0, pool_timeout=5)
        # Verify connection
        with eng.connect() as conn:
            pass
        return eng
    except Exception:
        # Fallback to local SQLite if PostgreSQL server is unreachable
        sqlite_engine = create_engine("sqlite:///./sql_app.db", connect_args={"check_same_thread": False})
        sql_file = Path(__file__).resolve().parent.parent / "database" / "database.sql"
        if sql_file.exists():
            try:
                raw_conn = sqlite_engine.raw_connection()
                with open(sql_file, "r", encoding="utf-8") as f:
                    raw_conn.executescript(f.read())
                raw_conn.commit()
                raw_conn.close()
            except Exception:
                pass
        return sqlite_engine

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
