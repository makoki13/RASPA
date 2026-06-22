import geopandas as gpd

ruta_archivo = 'data/municipios_esp.shp'
mapa_esp = gpd.read_file(ruta_archivo)

print("🔍 MOSTRANDO DATOS EN CRUDO (10 primeros municipios):")
print("-" * 80)

# Seleccionamos solo las columnas que nos importan para ver qué forma tienen
columnas_interes = ['NAMEUNIT', 'NATCODE', 'CODNUT2', 'CODNUT3']
print(mapa_esp[columnas_interes].head(10))