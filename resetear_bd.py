import sqlite3
import os
import geopandas as gpd

# (He incluido aquí los diccionarios de traducción NUTS para que este script sea 100% independiente)
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

RUTA_BD = 'data/raspa_db.sqlite'
RUTA_SHAPEFILE = 'data/municipios_esp.shp'

def resetear_base_de_datos():
    print("🗑️  Iniciando proceso de reseteo de RASPA...\n")

    # 1. BORRAR LA BASE DE DATOS ANTIGUA
    if os.path.exists(RUTA_BD):
        os.remove(RUTA_BD)
        print("✅ Base de datos antigua eliminada.")
    else:
        print("ℹ️  No existía base de datos previa (empezando desde cero).")

    # 2. CREAR NUEVA CONEXIÓN Y TABLAS
    conn = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()

    print("📁 Creando esquema de tablas limpio...")
    
    # Tablas Geográficas
    cursor.execute('''CREATE TABLE ccaa (id TEXT PRIMARY KEY, nombre TEXT)''')
    cursor.execute('''CREATE TABLE provincias (id TEXT PRIMARY KEY, nombre TEXT, id_ccaa TEXT, FOREIGN KEY(id_ccaa) REFERENCES ccaa(id))''')
    cursor.execute('''CREATE TABLE municipios (codigo_ign TEXT PRIMARY KEY, nombre TEXT, id_provincia TEXT, FOREIGN KEY(id_provincia) REFERENCES provincias(id))''')
    
    # Tablas de Juego
    cursor.execute('''CREATE TABLE usuarios (email TEXT PRIMARY KEY, nombre_publico TEXT, puntos_totales INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE municipios_visitados (email_usuario TEXT, codigo_ign_municipio TEXT, PRIMARY KEY (email_usuario, codigo_ign_municipio), FOREIGN KEY (email_usuario) REFERENCES usuarios(email), FOREIGN KEY (codigo_ign_municipio) REFERENCES municipios(codigo_ign))''')

    # 3. POBLAR CCAA Y PROVINCIAS
    print("🏛️  Insertando Comunidades Autónomas y Provincias...")
    for id_nut, nombre in CCAA_NOMBRES.items():
        cursor.execute("INSERT INTO ccaa (id, nombre) VALUES (?, ?)", (id_nut, nombre))

    for id_nut, nombre in PROVINCIAS_NOMBRES.items():
        id_ccaa = id_nut[:4]
        cursor.execute("INSERT INTO provincias (id, nombre, id_ccaa) VALUES (?, ?, ?)", (id_nut, nombre, id_ccaa))

    # 4. POBLAR MUNICIPIOS DESDE EL SHAPEFILE
    print("🗺️  Leyendo Shapefile e insertando Municipios...")
    if not os.path.exists(RUTA_SHAPEFILE):
        print(f"❌ ERROR CRÍTICO: No encuentro el archivo {RUTA_SHAPEFILE}")
        conn.close()
        return

    gdf = gpd.read_file(RUTA_SHAPEFILE)
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
    
    print("\n" + "="*50)
    print("🏆 ¡BASE DE DATOS RESETEADA CON ÉXITO!")
    print("="*50)
    print(f"   - {len(CCAA_NOMBRES)} Comunidades Autónomas")
    print(f"   - {len(PROVINCIAS_NOMBRES)} Provincias")
    print(f"   - {municipios_insertados} Municipios")
    print("   - 0 Usuarios (Lista para registrar nuevos ciclistas)\n")

if __name__ == "__main__":
    resetear_base_de_datos()