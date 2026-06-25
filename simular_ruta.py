import sqlite3
import os
from motor_geografico import procesar_ruta_gpx

def procesar_usuario(email_usuario, nombre_usuario, ruta_gpx):
    # Conexión a la base de datos
    conn = sqlite3.connect('data/raspa_db.sqlite')
    cursor = conn.cursor()

    # 1. COMPROBAR SI EL USUARIO ESTÁ REGISTRADO EN LA WEB
    cursor.execute("SELECT email FROM usuarios WHERE email = ?", (email_usuario,))
    usuario_existe = cursor.fetchone()

    if not usuario_existe:
        # NUEVA LÓGICA: Si no existe, lo rechazamos educadamente
        print(f"❌ RECHAZADO: El correo {email_usuario} no está registrado en la web. Se ignora el GPX.")
        conn.close()
        return # Detenemos la ejecución para este GPX

    # 2. Si existe, continuamos con el proceso normal
    # (Usamos el nombre de la BD por si el del correo viene raro)
    nombre_bd = cursor.execute("SELECT nombre_publico FROM usuarios WHERE email = ?", (email_usuario,)).fetchone()[0]

    # 3. Procesar la ruta
    codigos_municipios = procesar_ruta_gpx(ruta_gpx)
    if not codigos_municipios:
        print("⚠️ La ruta no contiene puntos válidos.")
        conn.close()
        return

    # 4. Guardar municipios nuevos en la BD (evitando duplicados)
    nuevos = 0
    for codigo in codigos_municipios:
        cursor.execute("INSERT OR IGNORE INTO municipios_visitados (email_usuario, codigo_ign_municipio) VALUES (?, ?)", 
                       (email_usuario, codigo))
        if cursor.rowcount > 0:
            nuevos += 1
    
    print(f"🆕 Municipios nuevos guardados para {email_usuario}: {nuevos}")

    if nuevos == 0:
        print("⚠️ Ya habías pasado por todos estos municipios. No hay puntos nuevos.")
        conn.close()
        return

    # ---------------------------------------------------------
    # 5. SISTEMA DE PUNTUACIÓN (Sin cambios aquí)
    # ---------------------------------------------------------
    puntos = 0
    print("\n📊 Calculando puntuación...")

    # A) 1 Punto por municipio único
    cursor.execute("SELECT COUNT(*) FROM municipios_visitados WHERE email_usuario = ?", (email_usuario,))
    total_municipios = cursor.fetchone()[0]
    puntos += total_municipios
    print(f"   + {total_municipios} puntos (Municipios únicos totales)")

    # B) Bonificación por completar una Provincia
    cursor.execute("SELECT id FROM provincias")
    provincias = cursor.fetchall()
    
    for (id_prov,) in provincias:
        cursor.execute("SELECT COUNT(*) FROM municipios WHERE id_provincia = ?", (id_prov,))
        total_en_prov = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(*) FROM municipios_visitados mv 
            JOIN municipios m ON mv.codigo_ign_municipio = m.codigo_ign 
            WHERE mv.email_usuario = ? AND m.id_provincia = ?
        ''', (email_usuario, id_prov))
        visitados_en_prov = cursor.fetchone()[0]

        if total_en_prov > 0 and visitados_en_prov == total_en_prov:
            puntos += total_en_prov
            cursor.execute("SELECT nombre FROM provincias WHERE id = ?", (id_prov,))
            nombre_prov = cursor.fetchone()[0]
            print(f"   + {total_en_prov} puntos (¡PROVINCIA COMPLETADA: {nombre_prov}!)")

    # C) Bonificación por completar una Comunidad Autónoma
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
        ''', (email_usuario, id_ccaa))
        visitados_en_ccaa = cursor.fetchone()[0]

        if total_en_ccaa > 0 and visitados_en_ccaa == total_en_ccaa:
            puntos += total_en_ccaa
            cursor.execute("SELECT nombre FROM ccaa WHERE id = ?", (id_ccaa,))
            nombre_ccaa = cursor.fetchone()[0]
            print(f"   + {total_en_ccaa} puntos (¡¡CCAA COMPLETADA: {nombre_ccaa}!!)")

    # 6. Actualizar el total en la tabla de usuarios
    cursor.execute("UPDATE usuarios SET puntos_totales = ? WHERE email = ?", (puntos, email_usuario))
    
    conn.commit()
    conn.close()
    
    print(f"\n🏆 PUNTUACIÓN TOTAL ACTUALIZADA PARA {nombre_bd}: {puntos} puntos\n")