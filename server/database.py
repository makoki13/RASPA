from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# La ruta a tu base de datos SQLite actual.
# Como ejecutamos uvicorn desde la raíz del proyecto, la ruta relativa es data/raspa_db.sqlite
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/raspa_db.sqlite"

# Creamos el motor (Engine). 
# check_same_thread=False es obligatorio para SQLite con FastAPI, ya que FastAPI atiende múltiples peticiones a la vez.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Creamos una fábrica de sesiones. Una "sesión" es la conexión abierta mientras hacemos cosas.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# La clase Base de la que heredarán nuestros modelos (tablas)
Base = declarative_base()