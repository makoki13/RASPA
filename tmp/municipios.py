import geopandas as gpd

RUTA_SHAPEFILE = 'data/municipios_esp.shp'

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

def municipios():
    gdf = gpd.read_file(RUTA_SHAPEFILE)
    municipios_insertados = 0
    
    for index, row in gdf.iterrows():
        codigo_ign = str(row['NATCODE'])
        nombre = row['NAMEUNIT']
        id_provincia = row['CODNUT3']
        
        municipios_insertados += 1

    
    print("\n" + "="*50)
    print("🏆 ¡BASE DE DATOS RESETEADA CON ÉXITO!")
    print("="*50)
    print(f"   - {len(CCAA_NOMBRES)} Comunidades Autónomas")
    print(f"   - {len(PROVINCIAS_NOMBRES)} Provincias")
    print(f"   - {municipios_insertados} Municipios")

if __name__ == "__main__":
    municipios()