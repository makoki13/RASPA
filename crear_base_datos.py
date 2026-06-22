import sqlite3
import geopandas as gpd
import os

# 1. Diccionarios de traducción NUTS -> Nombres en español
# (He puesto los del noroeste que han salido en tu prueba, y algunos más como ejemplo)
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
    # Si al ejecutar te da error de que falta alguna, simplemente búscala y añádela aquí
}

def crear_bd():
    # Eliminar la BD si existe para empezar limpio (solo para desarrollo)
    if os.path.exists('data/raspa_db.sqlite'):
        os.remove('data/raspa_db.sqlite')

    # Conectar a SQLite
    conn = sqlite3.connect('data/raspa_db.sqlite')
    cursor = conn.cursor()

    print("📁 Creando tablas...")
    # Crear tablas adaptadas a los códigos del IGN
    cursor.execute('''CREATE TABLE ccaa (id TEXT PRIMARY KEY, nombre TEXT)''')
    cursor.execute('''CREATE TABLE provincias (id TEXT PRIMARY KEY, nombre TEXT, id_ccaa TEXT, FOREIGN KEY(id_ccaa) REFERENCES ccaa(id))''')
    cursor.execute('''CREATE TABLE municipios (codigo_ign TEXT PRIMARY KEY, nombre TEXT, id_provincia TEXT, FOREIGN KEY(id_provincia) REFERENCES provincias(id))''')

    # Insertar CCAA
    print("🏛️ Insertando Comunidades Autónomas...")
    for id_nut, nombre in CCAA_NOMBRES.items():
        cursor.execute("INSERT INTO ccaa (id, nombre) VALUES (?, ?)", (id_nut, nombre))

    # Insertar Provincias
    print("📍 Insertando Provincias...")
    for id_nut, nombre in PROVINCIAS_NOMBRES.items():
        # Extraer el id de la CCAA (los 4 primeros caracteres, ej: 'ES521' -> 'ES52')
        id_ccaa = id_nut[:4]
        cursor.execute("INSERT INTO provincias (id, nombre, id_ccaa) VALUES (?, ?, ?)", (id_nut, nombre, id_ccaa))

    # Insertar Municipios desde el Shapefile
    print("🗺️ Leyendo Shapefile e insertando Municipios (Esto puede tardar unos segundos)...")
    gdf = gpd.read_file('data/municipios_esp.shp')

    municipios_insertados = 0
    for index, row in gdf.iterrows():
        codigo_ign = str(row['NATCODE'])
        nombre = row['NAMEUNIT']
        id_provincia = row['CODNUT3']

        cursor.execute("INSERT OR IGNORE INTO municipios (codigo_ign, nombre, id_provincia) VALUES (?, ?, ?)", 
                       (codigo_ign, nombre, id_provincia))
        municipios_insertados += 1

    conn.commit()
    conn.close()
    
    print(f"✅ ¡Base de datos creada con éxito!")
    print(f"   - {len(CCAA_NOMBRES)} Comunidades Autónomas")
    print(f"   - {len(PROVINCIAS_NOMBRES)} Provincias")
    print(f"   - {municipios_insertados} Municipios")

if __name__ == "__main__":
    crear_bd()