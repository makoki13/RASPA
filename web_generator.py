import sqlite3
import os
from jinja2 import Environment, FileSystemLoader

def generar_web():
    print("🖥️ Generando la página web del ranking...")
    
    # 1. Conectar a la BD y sacar el ranking ordenado por puntos
    conn = sqlite3.connect('data/raspa_db.sqlite')
    cursor = conn.cursor()
    
    cursor.execute("SELECT nombre_publico, puntos_totales FROM usuarios ORDER BY puntos_totales DESC")
    datos_ranking = cursor.fetchall()
    conn.close()

    # Formatear los datos para que Jinja2 los entienda bien
    ranking_list = []
    for nombre, puntos in datos_ranking:
        ranking_list.append({
            "nombre": nombre,
            "puntos": puntos
        })

    # 2. Configurar Jinja2 para que lea la carpeta 'templates'
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('ranking.html')

    # 3. Mezclar el HTML con los datos
    html_final = template.render(ranking=ranking_list)

    # 4. Guardar el resultado en la carpeta de salida
    ruta_salida = 'output_web/index.html'
    
    # Crear la carpeta si no existe
    os.makedirs('output_web', exist_ok=True)
    
    with open(ruta_salida, 'w', encoding='utf-8') as f:
        f.write(html_final)

    print(f"✅ Web generada correctamente en: {ruta_salida}")

if __name__ == "__main__":
    generar_web()