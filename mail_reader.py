import imaplib
import email
import os
from email.header import decode_header

# ==========================================
# CONFIGURACIÓN DE TU CORREO
# ==========================================
EMAIL_USER = "raspagpx@gmail.com"  # <-- CAMBIA ESTO
EMAIL_PASS = "fmla nolb ztab akii" 
IMAP_SERVER = "imap.gmail.com"
CARPETA_DESCARGA = "gpx_temp"

# Palabra clave que debe llevar el asunto para que el bot lo procese
ASUNTO_ESPERADO = "RASPA" 


def descargar_adjuntos():
    print("📬 Conectando al buzón de correo...")
    
    # Conectar y loguearse
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        print("✅ Conexión exitosa.")
    except Exception as e:
        print(f"❌ Error al conectarse: {e}")
        return []

    # Seleccionar la bandeja de entrada
    mail.select("inbox")

    # Buscar correos NO LEÍDOS (UNSEEN) que contengan "RASPA" en el asunto
    status, mensajes = mail.search(None, f'(UNSEEN SUBJECT "{ASUNTO_ESPERADO}")')
    ids_correos = mensajes[0].split()

    if not ids_correos:
        print("📭 No hay nuevas rutas en el buzón.")
        mail.logout()
        return []

    print(f"🚴 ¡Se encontraron {len(ids_correos)} ruta(s) nueva(s)! Procesando...\n")
    
    rutas_procesadas = []

    for num in ids_correos:
        # Obtener el correo completo
        status, datos_correo = mail.fetch(num, "(RFC822)")
        
        # Buscamos la parte que realmente contiene el correo (ignorando basura residual de IMAP)
        raw_email = None
        for response_part in datos_correo:
            if isinstance(response_part, tuple):
                raw_email = response_part[1]
                break
        
        # Si por alguna razón no se pudo leer, saltamos a el siguiente correo
        if raw_email is None:
            print("      ⚠️ Error al leer el contenido del correo.")
            continue

        mensaje = email.message_from_bytes(raw_email)
        # 1. Sacar el remitente (Para saber qué usuario es)
        remitente_crudo = mensaje["From"]
        # Limpiar el remitente para quedarnos solo con el email
        if "<" in remitente_crudo and ">" in remitente_crudo:
            email_usuario = remitente_crudo.split("<")[1].split(">")[0]
        else:
            email_usuario = remitente_crudo

        print(f"   -> Ruta de: {email_usuario}")

        # 2. Buscar el adjunto .gpx
        gpx_encontrado = False
        for parte in mensaje.walk():
            # Si es un adjunto
            if parte.get_content_maintype() == "multipart":
                continue
            if parte.get("Content-Disposition") is None:
                continue

            nombre_archivo = parte.get_filename()
            if nombre_archivo:
                # Decodificar el nombre del archivo (a veces viene en raro)
                nombre_archivo, encoding = decode_header(nombre_archivo)[0]
                if isinstance(nombre_archivo, bytes):
                    nombre_archivo = nombre_archivo.decode(encoding or "utf-8")

                # Si es un GPX, lo guardamos
                if nombre_archivo.lower().endswith(".gpx"):
                    gpx_encontrado = True
                    # Generar un nombre único para no sobreescribir si dos usuarios envían "ruta.gpx"
                    nombre_guardado = f"{email_usuario.replace('@', '_at_')}_{nombre_archivo}"
                    ruta_guardado = os.path.join(CARPETA_DESCARGA, nombre_guardado)

                                        # Extraer el contenido y asegurarnos de que son bytes
                    archivo_bytes = parte.get_payload(decode=True)
                    
                    if isinstance(archivo_bytes, bytes):
                        # Guardar el archivo
                        with open(ruta_guardado, "wb") as f:
                            f.write(archivo_bytes)
                    else:
                        print("      ⚠️ Error: El adjunto no se pudo leer como archivo binario.")
                    
                    print(f"      ✅ GPX guardado como: {nombre_guardado}")
                    rutas_procesadas.append((email_usuario, ruta_guardado))

        if not gpx_encontrado:
            print(f"      ⚠️ El correo no contenía ningún archivo .gpx adjunto.")

        # 3. Marcar el correo como LEÍDO para no procesarlo de nuevo
        mail.store(num, "+FLAGS", "\\Seen")

    # Cerrar conexión
    mail.close()
    mail.logout()
    print("\n🔶 Buzón actualizado.")
    return rutas_procesadas


# --- PRUEBA DEL SCRIPT ---
if __name__ == "__main__":
    descargar_adjuntos()