import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sys

# Asegurar que encuentra la raíz del proyecto
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import DATA_DIR

# LA MAGIA: ¿Estamos en la nube (Render) o en local?
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # No hay variable de entorno -> Estamos en local -> Usamos SQLite
    ruta_sqlite = DATA_DIR / 'raspa_db.sqlite'
    DATABASE_URL = f"sqlite:///{ruta_sqlite}"
    motor_kwargs = {"connect_args": {"check_same_thread": False}}
else:
    # Hay variable de entorno -> Estamos en Render -> Usamos PostgreSQL
    motor_kwargs = {}

# Crear el motor
engine = create_engine(DATABASE_URL, **motor_kwargs)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase Base
Base = declarative_base()

# Importar modelos para que sepan de las tablas
from server import models

# Crear las tablas si no existen (vital para PostgreSQL en la nube)
Base.metadata.create_all(bind=engine)
