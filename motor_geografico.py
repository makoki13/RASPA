import gpxpy
import geopandas as gpd
from shapely.geometry import Point

def procesar_ruta_gpx(ruta_archivo):
    print(f"\n📂 Leyendo archivo GPX: {ruta_archivo}...")
    
    # 1. PARSEAR EL GPX (Extraer latitudes y longitudes)
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        gpx = gpxpy.parse(f)

    puntos = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                # GeoPandas usa el orden (Longitud, Latitud) = (X, Y)
                puntos.append((point.longitude, point.latitude))

    if not puntos:
        print("❌ Error: El GPX no tiene puntos de tracks.")
        return []

    print(f"✅ Extraídos {len(puntos)} puntos del GPS.")

    # 2. CRUCE GEOGRÁFICO (La magia de GeoPandas)
    print("🗺️ Calculando intersección con los municipios de España...")
    # Cargamos tu Shapefile del IGN
    mapa_esp = gpd.read_file('data/municipios_esp.shp')

    # Convertimos la lista de coordenadas del GPX en una geometría de puntos
    geometria_puntos = [Point(lon, lat) for lon, lat in puntos]
    
    # Creamos un GeoDataFrame temporal con los puntos del ciclista
    # Le decimos que el sistema de coordenadas es WGS84 (el que usan los GPS)
    gdf_puntos = gpd.GeoDataFrame(geometry=geometria_puntos, crs="EPSG:4326")

    # SPATIAL JOIN: Por cada punto del ciclista, busca en qué polígono (municipio) cae
    # predicate="within" significa "el punto está completamente dentro del municipio"
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

# --- PRUEBA DEL SCRIPT ---
if __name__ == "__main__":
    # Pon aquí el nombre del archivo que hayas metido en gpx_temp/
    archivo_a_probar = 'gpx_temp/prueba_ruta.gpx' 
    
    try:
        codigos_municipios = procesar_ruta_gpx(archivo_a_probar)
        print("\n💡 Lista de códigos IGN para la base de datos:")
        print(codigos_municipios)
    except FileNotFoundError:
        print(f"❌ No encuentro el archivo {archivo_a_probar}. Asegúrate de poner un GPX real en la carpeta gpx_temp/")