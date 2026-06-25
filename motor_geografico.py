import gpxpy
import geopandas as gpd
from shapely.geometry import Point
import sys
import os

# ==========================================================
# IMPORTANTE: Configurar rutas absolutas para la nube (Render)
# ==========================================================
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import DATA_DIR


def procesar_ruta_gpx(ruta_archivo):
    print(f"\n📂 Leyendo archivo GPX: {ruta_archivo}...")
    
    # 1. PARSEAR EL GPX (Extraer latitudes y longitudes)
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            gpx = gpxpy.parse(f)
    except Exception as e:
        print(f"❌ Error al leer el archivo GPX: {e}")
        return []

    puntos = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                # GeoPandas usa el orden (X, Y) = (Longitud, Latitud)
                puntos.append((point.longitude, point.latitude))

    if not puntos:
        print("❌ Error: El GPX no tiene puntos de tracks.")
        return []

    print(f"✅ Extraídos {len(puntos)} puntos del GPS.")

    # 2. CRUCE GEOGRÁFICO (La magia de GeoPandas)
    print("🗺️ Calculando intersección con los municipios de España...")
    
    # Usar la ruta absoluta garantizada por paths.py
    ruta_shapefile = DATA_DIR / 'municipios_esp.shp'
    
    try:
        mapa_esp = gpd.read_file(ruta_shapefile)
    except Exception as e:
        print(f"❌ Error crítico: No se pudo cargar el mapa de España en {ruta_shapefile}. Error: {e}")
        return []

    # Convertimos la lista de coordenadas del GPX en una geometría de puntos
    geometria_puntos = [Point(lon, lat) for lon, lat in puntos]
    
    # Creamos un GeoDataFrame temporal con los puntos del ciclista
    # Le decimos que el sistema de coordenadas es WGS84 (el que usan los GPS)
    gdf_puntos = gpd.GeoDataFrame(geometry=geometria_puntos, crs="EPSG:4326")

    # Aseguramos que ambos mapas usan el mismo sistema de coordenadas (WGS84)
    mapa_esp = mapa_esp.to_crs(epsg=4326)

    # SPATIAL JOIN
    puntos_en_municipios = gpd.sjoin(gdf_puntos, mapa_esp, how="inner", predicate="within")

    # 3. LIMPIEZA Y RESULTADO
    # Sacamos la columna NATCODE (nuestro ID de municipio) y eliminamos duplicados
    municipios_unicos = puntos_en_municipios['NATCODE'].unique().tolist()

    print(f"🏁 ¡Cálculo terminado! Has pasado por {len(municipios_unicos)} municipios diferentes.\n")
    
    # Opcional: Mostrar los nombres de los municipios para comprobar que funciona
    for codigo in municipios_unicos:
        fila = mapa_esp[mapa_esp['NATCODE'] == codigo].iloc[0]
        print(f"   - {fila['NAMEUNIT']}")

    return municipios_unicos