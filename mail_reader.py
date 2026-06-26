import email
import imaplib
import os
from email.header import decode_header

# ==========================================
# CONFIGURACIÓN DE TU CORREO
# ==========================================
EMAIL_USER = "raspagpx@gmail.com"  # <-- CAMBIA ESTO
EMAIL_PASS = "fmla nolb ztab akii"        # <-- LA CONTRASEÑA DE APLICACIÓN
IMAP_SERVER = "imap.gmail.com"
CARPETA_DESCARGA = "gpx_temp"

# Ya no necesitamos el asunto. Aceptamos TODO lo que llegue.
# Si no tiene GPX, el propio bucle lo detectará y lo ignorará.


def descargar_adjuntos():  # noqa: C901
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
    mail.select("INBOX")

    # BUSCAR TODOS LOS CORREOS NO LEÍDOS (Ya no miramos el asunto)
    status, mensajes = mail.search(None, "UNSEEN")
    ids_correos = mensajes[0].split()

    if not ids_correos:
        print("📭 No hay nuevos correos en el buzón.")
        mail.logout()
        return []

    print(f"🚴 ¡Se encontraron {len(ids_correos)} correo(s) nuevo(s). Analizando adjuntos...\n")

    rutas_procesadas = []

    for num in ids_correos:
        # Obtener el correo completo
        status, datos_correo = mail.fetch(num, "(RFC822)")
        mensaje = email.message_from_bytes(datos_correo[0][1]) # type: ignore

        # 1. Sacar el remitente (Para saber qué usuario es)
        remitente_crudo = mensaje["From"]
        if "<" in remitente_crudo and ">" in remitente_crudo:
            email_usuario = remitente_crudo.split("<")[1].split(">")[0]
        else:
            email_usuario = remitente_crudo

        print(f"   -> Analizando correo de: {email_usuario}")

        # 2. Buscar el/los adjunto/s .gpx
        gpx_encontrado = False

        for parte in mensaje.walk():
            # Si es un contenedor multipart, seguimos profundizando
            if parte.get_content_maintype() == "multipart":
                continue
            # Si no tiene cabecera de disposición, es el cuerpo del texto, lo saltamos
            if parte.get("Content-Disposition") is None:
                continue

            nombre_archivo = parte.get_filename()
            if nombre_archivo:
                # Decodificar el nombre del archivo (a veces viene en raro)
                nombre_archivo, encoding = decode_header(nombre_archivo)[0]
                if isinstance(nombre_archivo, bytes):
                    nombre_archivo = nombre_archivo.decode(encoding or "utf-8")

                # Si es un GPX, ¡lo procesamos!
                if nombre_archivo.lower().endswith(".gpx"):
                    gpx_encontrado = True

                    # Generar un nombre único para no sobreescribir si dos usuarios envían "ruta.gpx"
                    nombre_guardado = f"{email_usuario.replace('@', '_at_')}_{nombre_archivo}"
                    ruta_guardado = os.path.join(CARPETA_DESCARGA, nombre_guardado)

                    # Guardar el archivo
                    with open(ruta_guardado, "wb") as f:
                        f.write(parte.get_payload(decode=True)) # type: ignore

                    print(f"      ✅ GPX encontrado y guardado como: {nombre_guardado}")
                    rutas_procesadas.append((email_usuario, ruta_guardado))

        # 3. Evaluar qué hacer con el correo
        if gpx_encontrado:
            print("      🎯 Correo aceptado para procesamiento.")
        else:
            print("      ⚠️ El correo no contenía ningún archivo .gpx adjunto. Ignorado.")

        # 4. MARCAR EL CORREO COMO LEÍDO
        # (Tanto si tiene GPX como si no lo tiene, para que Gmail lo quite de la bandeja de entrada)
        mail.store(num, "+FLAGS", "\\Seen")

    # Cerrar conexión
    mail.close()
    print("\n🔶 Buzón actualizado.")
    return rutas_procesadas


# --- PRUEBA DEL SCRIPT ---
if __name__ == "__main__":
    descargar_adjuntos()
