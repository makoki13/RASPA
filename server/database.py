import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# Importamos la ruta base
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import DATA_DIR

# Usamos la ruta absoluta
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATA_DIR / 'raspa_db.sqlite'}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()