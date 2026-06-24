from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from server.database import Base

class Ccaa(Base):
    __tablename__ = "ccaa"
    id = Column(String, primary_key=True, index=True)
    nombre = Column(String)
    
    # Relación: Una CCAA tiene muchas provincias
    provincias = relationship("Provincia", back_populates="ccaa")

class Provincia(Base):
    __tablename__ = "provincias"
    id = Column(String, primary_key=True, index=True)
    nombre = Column(String)
    id_ccaa = Column(String, ForeignKey("ccaa.id"))
    
    # Relaciones
    ccaa = relationship("Ccaa", back_populates="provincias")
    municipios = relationship("Municipio", back_populates="provincia")

class Municipio(Base):
    __tablename__ = "municipios"
    codigo_ign = Column(String, primary_key=True, index=True)
    nombre = Column(String)
    id_provincia = Column(String, ForeignKey("provincias.id"))
    
    # Relaciones
    provincia = relationship("Provincia", back_populates="municipios")

class Usuario(Base):
    __tablename__ = "usuarios"
    email = Column(String, primary_key=True, index=True)
    nombre_publico = Column(String)
    puntos_totales = Column(Integer, default=0)
    password_hash = Column(String, default=None)

class MunicipioVisitado(Base):
    __tablename__ = "municipios_visitados"
    email_usuario = Column(String, ForeignKey("usuarios.email"), primary_key=True)
    codigo_ign_municipio = Column(String, ForeignKey("municipios.codigo_ign"), primary_key=True)