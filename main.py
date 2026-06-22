from mail_reader import descargar_adjuntos
from simular_ruta import procesar_usuario
from web_generator import generar_web

def ejecutar_ciclo_raspa():
    print("="*50)
    print("🚴‍♂️ RASPA - Ciclo de ejecución automática")
    print("="*50 + "\n")

    # 1. Buscar nuevos correos y descargar GPX
    rutas_recibidas = descargar_adjuntos()

    # 2. Si hay rutas nuevas, las procesamos
    if rutas_recibidas:
        for email_usuario, ruta_gpx in rutas_recibidas:
            print(f"\n⚙️ Procesando la ruta de {email_usuario}...")
            # Nos quedamos solo con la parte antes de la @ para el nombre público
            nombre_usuario = email_usuario.split('@')[0]
            procesar_usuario(email_usuario, nombre_usuario, ruta_gpx)
            
            # Borramos el GPX de la carpeta temporal tras procesarlo para no llenar el disco
            import os
            try:
                os.remove(ruta_gpx)
            except:
                pass

    # 3. Siempre regeneramos la web (por si hemos actualizado puntos)
    generar_web()
    print("\n🏁 Ciclo completado. Pausa hasta la próxima ejecución.\n")

if __name__ == "__main__":
    ejecutar_ciclo_raspa()