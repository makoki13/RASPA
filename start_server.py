import os
import sys

# Asegurarnos de que Python encuentra la raíz del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subprocess
import threading
import time
import uvicorn

# 1. FORZAR LA CREACIÓN DE LA BASE DE DATOS ANTES DE NADA
print("🛠️ Verificando/Creando tablas de la base de datos en la nube...")
from server import database, models
database.Base.metadata.create_all(bind=database.engine)
print("✅ Base de datos verificada.")

from server import database, models
database.Base.metadata.create_all(bind=database.engine)
print("✅ Base de datos verificada.")

# NUEVO: Comprobar si hay que poblarla
from sqlalchemy import func
db_check = database.SessionLocal()
if db_check.query(func.count(models.Municipio.id)).scalar() == 0:
    print("⚠️ Base de datos vacía. Ejecutando script de poblamiento...")
    db_check.close()
    from poblar_db import poblar_base_datos
    poblar_base_datos()
else:
    db_check.close()
    print("✅ Base de datos contiene municipios, saltando poblamiento.")

# 2. Ahora sí, importamos la app de FastAPI
from server.main import app

def run_bot():
    """Ejecuta el bot en un hilo secundario cada 15 minutos"""
    while True:
        print("☕ Iniciando ciclo del bot en la nube...")
        try:
            # Ejecuta main.py como un script independiente
            subprocess.run(["python", "main.py"], check=True)
        except Exception as e:
            print(f"Error en el bot: {e}")
        
        print("😴 Bot durmiendo 15 minutos...")
        time.sleep(15 * 60) # 15 minutos

if __name__ == "__main__":
    # 3. Lanzamos el bot en un hilo paralelo para que no bloquee la web
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 4. Lanzamos el servidor web en el hilo principal
    print("🚀 Arrancando servidor web RASPA...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))