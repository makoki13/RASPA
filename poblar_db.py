import sys
import os
import geopandas as gpd
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from server.database import SessionLocal
from server import models

# Diccionarios para traducir los códigos NUTS del IGN a nombres reales
CCAA_NOMBRES = {
    'ES11': 'Galicia', 'ES12': 'Principado de Asturias', 'ES13': 'Cantabria',
    'ES21': 'País Vasco', 'ES22': 'Comunidad Foral de Navarra', 'ES23': 'La Rioja',
    'ES24': 'Aragón', 'ES30': 'Comunidad de Madrid', 'ES41': 'Castilla y León',
    'ES42': 'Castilla-La Mancha', 'ES43': 'Extremadura', 'ES51': 'Cataluña',
    'ES52': 'Comunidad Valenciana', 'ES53': 'Illes Balears', 'ES61': 'Andalucía',
    'ES62': 'Región de Murcia', 'ES63': 'Ciudad Autónoma de Ceuta', 'ES64': 'Ciudad Autónoma de Melilla',
    'ES70': 'Canarias'
}

PROVINCIAS_NOMBRES = {
    'ES110': 'A Coruña', 'ES111': 'Lugo', 'ES112': 'Ourense', 'ES113': 'Pontevedra',
    'ES120': 'Asturias', 'ES130': 'Cantabria',
    'ES211': 'Araba/Álava', 'ES212': 'Gipuzkoa', 'ES213': 'Bizkaia',
    'ES220': 'Navarra', 'ES230': 'La Rioja',
    'ES241': 'Huesca', 'ES242': 'Teruel', 'ES243': 'Zaragoza',
    'ES300': 'Madrid',
    'ES411': 'Ávila', 'ES412': 'Burgos', 'ES413': 'León', 'ES414': 'Palencia', 
    'ES415': 'Salamanca', 'ES416': 'Segovia', 'ES417': 'Soria', 'ES418': 'Valladolid', 'ES419': 'Zamora',
    'ES421': 'Albacete', 'ES422': 'Ciudad Real', 'ES423': 'Cuenca', 'ES424': 'Guadalajara', 'ES425': 'Toledo',
    'ES431': 'Badajoz', 'ES432': 'Cáceres',
    'ES511': 'Barcelona', 'ES512': 'Girona', 'ES513': 'Lleida', 'ES514': 'Tarragona',
    'ES521': 'Alicante', 'ES522': 'Castellón', 'ES523': 'Valencia',
    'ES531': 'Illes Balears',
    'ES611': 'Almería', 'ES612': 'Cádiz', 'ES613': 'Córdoba', 'ES614': 'Granada', 
    'ES615': 'Huelva', 'ES616': 'Jaén', 'ES617': 'Málaga', 'ES618': 'Sevilla',
    'ES620': 'Murcia',
    'ES630': 'Ceuta', 'ES640': 'Melilla',
    'ES701': 'Las Palmas', 'ES702': 'Santa Cruz de Tenerife',
}

def poblar_base_datos():
    print("📂 Leyendo Shapefile desde data/municipios_esp.shp...")
    from paths import DATA_DIR
    gdf = gpd.read_file(DATA_DIR / 'municipios_esp.shp')
    
    db: Session = SessionLocal()
    try:
        # 1. Poblar CCAA
        print("🏛️  Insertando Comunidades Autónomas...")
        for id_nut, nombre in CCAA_NOMBRES.items():
            ccaa = models.Ccaa(id=id_nut, nombre=nombre)
            db.add(ccaa)
        
        # 2. Poblar Provincias
        print("📍 Insertando Provincias...")
        for id_nut, nombre in PROVINCIAS_NOMBRES.items():
            id_ccaa = id_nut[:4]
            prov = models.Provincia(id=id_nut, nombre=nombre, id_ccaa=id_ccaa)
            db.add(prov)

        # 3. Poblar Municipios
        print("🗺️  Insertando Municipios (Esto tarda unos segundos)...")
        contador = 0
        for index, row in gdf.iterrows():
            codigo_ign = str(row['NATCODE'])
            nombre = row['NAMEUNIT']
            id_provincia = row['CODNUT3']
            
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