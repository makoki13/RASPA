import sys
import os
import geopandas as gpd
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server.database import SessionLocal
from server import models

def poblar_base_datos():
    print("📂 Leyendo Shapefile desde data/municipios_esp.shp...")
    from paths import DATA_DIR
    gdf = gpd.read_file(DATA_DIR / 'municipios_esp.shp')
    
    db: Session = SessionLocal()
    try:
        # 1. Poblar CCAA (Dinámico: extraemos los códigos NUTS2 únicos del archivo)
        print("🏛️  Insertando Comunidades Autónomas...")
        ccaas_unicos = gdf['CODNUT2'].unique()
        for id_nut in ccaas_unicos:
            # Usamos el código NUTS2 como nombre si no hay otra cosa
            ccaa = models.Ccaa(id=str(id_nut), nombre=str(id_nut))
            db.add(ccaa)
        
        # 2. Poblar Provincias (Dinámico: extraemos los códigos NUTS3 únicos del archivo)
        print("📍 Insertando Provincias...")
        provincias_unicos = gdf['CODNUT3'].unique()
        for id_nut in provincias_unicos:
            id_ccaa = str(id_nut)[:4]
            # Usamos el código NUTS3 como nombre si no hay otra cosa
            prov = models.Provincia(id=str(id_nut), nombre=str(id_nut), id_ccaa=id_ccaa)
            db.add(prov)

        # Hacemos un flush intermedio para asegurarnos de que CCAA y Provincias existen antes de los municipios
        db.flush()

        # 3. Poblar Municipios
        print("🗺️  Insertando Municipios (Esto tarda unos segundos)...")
        contador = 0
        for index, row in gdf.iterrows():
            codigo_ign = str(row['NATCODE'])
            nombre = row['NAMEUNIT']
            id_provincia = str(row['CODNUT3'])
            
            municipio = models.Municipio(codigo_ign=codigo_ign, nombre=nombre, id_provincia=id_provincia)
            db.add(municipio)
            contador += 1
            
        db.commit()
        print(f"✅ ¡Base de datos poblada con éxito! ({contador} municipios)")
        
    except Exception as e:
        print(f"❌ Error al poblar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    poblar_base_datos()