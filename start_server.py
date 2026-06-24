import os
import subprocess
import threading
import time
import uvicorn
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
    # 1. Lanzamos el bot en un hilo paralelo para que no bloquee la web
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 2. Lanzamos el servidor web en el hilo principal
    print("🚀 Arrancando servidor web RASPA...")
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))