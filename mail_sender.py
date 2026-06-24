import smtplib
import ssl
from email.message import EmailMessage

# Configuración del correo (el bot que creamos)
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def enviar_correo_bienvenida(destinatario, password):
    print(f"   📧 Enviando correo de bienvenida a {destinatario}...")
    
    asunto = "¡Bienvenido a RASPA! Tu clave de acceso."
    cuerpo = f"""
    Hola ciclista,

    Tu ruta ha sido procesada correctamente y has sido dado de alta en el sistema RASPA (Race Across Spain).

    Aquí tienes tus credenciales para acceder a tu panel privado:
    - Correo: {destinatario}
    - Contraseña provisional: {password}

    Entra en la web e introduce estos datos. 
    (Próximamente podrás cambiar la contraseña desde tu panel).

    ¡A raspar municipios!
    El bot de RASPA.
    """
    
    # Construir el mensaje
    msg = EmailMessage()
    msg['Subject'] = asunto
    msg['From'] = EMAIL_USER
    msg['To'] = destinatario
    msg.set_content(cuerpo)

    # Conectar con Gmail de forma segura y enviar
    contexto_seguro = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=contexto_seguro) as servidor:
        servidor.login(EMAIL_USER, EMAIL_PASS)
        servidor.send_message(msg)
        
    print(f"   ✅ Correo enviado con éxito.")