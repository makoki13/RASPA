import sqlite3
from motor_geografico import procesar_ruta_gpx # Importamos la magia que ya funciona

def procesar_usuario(email, nombre, ruta_gpx):
    conn = sqlite3.connect('data/raspa_db.sqlite')
    cursor = conn.cursor()

    # 1. Registrar usuario si no existe
    cursor.execute("INSERT OR IGNORE INTO usuarios (email, nombre_publico) VALUES (?, ?)", (email, nombre))

    # 2. Obtener municipios del GPX (usando nuestro script de la Fase 2)
    codigos_municipios = procesar_ruta_gpx(ruta_gpx)
    if not codigos_municipios:
        print("No se procesaron municipios. Saliendo.")
        conn.close()
        return

    # 3. Guardar municipios nuevos en la BD (INSERT OR IGNORE evita duplicados)
    nuevos = 0
    for codigo in codigos_municipios:
        cursor.execute("INSERT OR IGNORE INTO municipios_visitados (email_usuario, codigo_ign_municipio) VALUES (?, ?)", 
                       (email, codigo))
        if cursor.rowcount > 0:
            nuevos += 1
    
    print(f"🆕 Municipios nuevos guardados para {email}: {nuevos}")

    if nuevos == 0:
        print("⚠️ Ya habías pasado por todos estos municipios. No hay puntos nuevos.")
        conn.close()
        return

    # ---------------------------------------------------------
    # 4. SISTEMA DE PUNTUACIÓN (La regla de RASPA)
    # ---------------------------------------------------------
    puntos = 0
    print("\n📊 Calculando puntuación...")

    # A) 1 Punto por municipio único
    cursor.execute("SELECT COUNT(*) FROM municipios_visitados WHERE email_usuario = ?", (email,))
    total_municipios = cursor.fetchone()[0]
    puntos += total_municipios
    print(f"   + {total_municipios} puntos (Municipios únicos totales)")

    # B) Bonificación por completar una Provincia 
    # (Se suman tantos puntos como municipios tenga esa provincia)
    cursor.execute("SELECT id FROM provincias")
    provincias = cursor.fetchall()
    
    for (id_prov,) in provincias:
        # ¿Cuántos municipios tiene esa provincia en total?
        cursor.execute("SELECT COUNT(*) FROM municipios WHERE id_provincia = ?", (id_prov,))
        total_en_prov = cursor.fetchone()[0]
        
        # ¿Cuántos de esos tiene el usuario?
        cursor.execute('''
            SELECT COUNT(*) FROM municipios_visitados mv 
            JOIN municipios m ON mv.codigo_ign_municipio = m.codigo_ign 
            WHERE mv.email_usuario = ? AND m.id_provincia = ?
        ''', (email, id_prov))
        visitados_en_prov = cursor.fetchone()[0]

        # Si ha visitado todos los de la provincia
        if total_en_prov > 0 and visitados_en_prov == total_en_prov:
            puntos += total_en_prov  # <-- AQUÍ ESTÁ EL CAMBIO: en vez de 100, sumamos el total
            cursor.execute("SELECT nombre FROM provincias WHERE id = ?", (id_prov,))
            nombre_prov = cursor.fetchone()[0]
            print(f"   + {total_en_prov} puntos (¡PROVINCIA COMPLETADA: {nombre_prov}! - {total_en_prov} municipios)")

    # C) Bonificación por completar una Comunidad Autónoma
    # (Se suman tantos puntos como municipios tenga esa CCAA)
    cursor.execute("SELECT id FROM ccaa")
    ccaas = cursor.fetchall()

    for (id_ccaa,) in ccaas:
        cursor.execute("SELECT COUNT(*) FROM municipios m JOIN provincias p ON m.id_provincia = p.id WHERE p.id_ccaa = ?", (id_ccaa,))
        total_en_ccaa = cursor.fetchone()[0]

        cursor.execute('''
            SELECT COUNT(*) FROM municipios_visitados mv 
            JOIN municipios m ON mv.codigo_ign_municipio = m.codigo_ign 
            JOIN provincias p ON m.id_provincia = p.id 
            WHERE mv.email_usuario = ? AND p.id_ccaa = ?
        ''', (email, id_ccaa))
        visitados_en_ccaa = cursor.fetchone()[0]

        if total_en_ccaa > 0 and visitados_en_ccaa == total_en_ccaa:
            puntos += total_en_ccaa  # <-- AQUÍ ESTÁ EL CAMBIO: en vez de 500, sumamos el total
            cursor.execute("SELECT nombre FROM ccaa WHERE id = ?", (id_ccaa,))
            nombre_ccaa = cursor.fetchone()[0]
            print(f"   + {total_en_ccaa} puntos (¡¡CCAA COMPLETADA: {nombre_ccaa}!! - {total_en_ccaa} municipios)")

    # 5. Actualizar el total en la tabla de usuarios
    cursor.execute("UPDATE usuarios SET puntos_totales = ? WHERE email = ?", (puntos, email))
    
    conn.commit()
    conn.close()
    
    print(f"\n🏆 PUNTUACIÓN TOTAL ACTUALIZADA PARA {nombre}: {puntos} puntos\n")


# --- PRUEBA ---
if __name__ == "__main__":
    # Simulamos que el usuario "pedro@gmail.com" envía la ruta que probaste antes
    email_prueba = "pedro@gmail.com"
    nombre_prueba = "Pedro El Raspador"
    archivo_prueba = "gpx_temp/prueba_ruta.gpx"

    procesar_usuario(email_prueba, nombre_prueba, archivo_prueba)