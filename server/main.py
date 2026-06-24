from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

# Importaciones de nuestros módulos
from server import models, database, security

app = FastAPI(title="RASPA API", description="Race Across Spain - Backend")

# Este objeto de FastAPI es el que busca la pulsera (Token) en las cabeceras de las peticiones
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Dependencia que abre y cierra la conexión a la base de datos
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# RUTAS PÚBLICAS (No requieren pulsera)
# ==========================================

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    La taquilla. FastAPI automáticamente leerá el email (username) y la contraseña 
    que el usuario envíe desde un formulario.
    """
    # 1. Buscar al usuario en la BD por su email
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    
    # 2. Sacamos el hash a una variable para evitar el error de Pylance con las Columnas de SQLAlchemy
    hash_guardado = usuario.password_hash if usuario else None
    
    # type: ignore es la forma profesional de decirle a Pylance "Cállate, yo sé que esto funciona"
    if not usuario or not hash_guardado or not security.verificar_password(form_data.password, hash_guardado): # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. Generar la pulsera (Token JWT)
    token_acceso = security.crear_token_acceso(data={"sub": usuario.email})
    
    # 5. Devolver la pulsera al usuario
    return {"access_token": token_acceso, "token_type": "bearer"}


@app.get("/ranking")
def obtener_ranking(db: Session = Depends(get_db)):
    """Devuelve el ranking público de todos los ciclistas."""
    usuarios = db.query(models.Usuario).order_by(models.Usuario.puntos_totales.desc()).all()
    # Comprehension list para convertir los objetos en diccionarios JSON
    resultado = [{"nombre": u.nombre_publico, "puntos": u.puntos_totales} for u in usuarios]
    return resultado


# ==========================================
# SISTEMA DE SEGURIDAD (El revisor de pulseras)
# ==========================================

def obtener_usuario_actual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Esta función se ejecuta ANTES de entrar a las rutas privadas.
    Si la pulsera es válida, devuelve el objeto del usuario.
    Si no, lanza un error 401.
    """
    try:
        # Intentamos leer la pulsera. Usamos las variables de config.py importadas en security.py
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido (falta el email interno)")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o ha caducado")
    
    # Si la pulsera es buena, buscamos al usuario en la BD para devolverlo entero
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="El usuario de la pulsera no existe en la BD")
    
    return usuario


# ==========================================
# RUTAS PRIVADAS (Requieren pulsera válida)
# ==========================================

@app.get("/perfil")
def ver_mi_perfil(usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    """
    Zona VIP. Para entrar aquí, el navegador DEBE enviar la pulsera en la cabecera.
    Fíjate que no tocamos la base de datos para buscar el usuario, 
    'obtener_usuario_actual' ya nos lo ha entregado limpio.
    """
    return {
        "mensaje": f"Hola {usuario_actual.nombre_publico}, has accedido a tu zona privada.",
        "tu_email_es": usuario_actual.email,
        "tus_puntos": usuario_actual.puntos_totales
    }