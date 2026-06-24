from sqlalchemy import func
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Importaciones de nuestros módulos
from server import models, database, security

app = FastAPI(title="RASPA API", description="Race Across Spain - Backend")
# Configurar Jinja2 para leer la carpeta de plantillas HTML
templates = Jinja2Templates(directory="templates")

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

@app.get("/", response_class=HTMLResponse)
def pagina_ranking_html(request: Request, db: Session = Depends(get_db)):
    """Pinta la página web del ranking"""
    usuarios = db.query(models.Usuario).order_by(models.Usuario.puntos_totales.desc()).all()
    resultado = [{"nombre": u.nombre_publico, "puntos": u.puntos_totales} for u in usuarios]
    
    # En lugar de devolver un JSON, devolvemos la plantilla HTML pasándole los datos
    return templates.TemplateResponse(request, "ranking.html", {"request": request, "ranking": resultado}) # type: ignore# ==========================================
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

@app.get("/panel")
@app.get("/panel", response_class=HTMLResponse)
def ver_panel_html(request: Request, db: Session = Depends(get_db)):
    # TEMPORAL: Simulamos que es Pablo para poder ver el HTML
    usuario_actual = db.query(models.Usuario).filter(models.Usuario.email == "pablo@ejemplo.com").first()
    """
    Pinta el panel de progreso del usuario con HTML.
    """
    email = usuario_actual.email # type: ignore
    resultado_panel = []

    ccaas = db.query(models.Ccaa).all()
    
    for ccaa in ccaas:
        total_ccaa = db.query(func.count(models.Municipio.codigo_ign)).join(models.Provincia).filter(models.Provincia.id_ccaa == ccaa.id).scalar()
        
        visitados_ccaa = db.query(func.count(models.Municipio.codigo_ign)).join(models.Provincia).join(models.MunicipioVisitado).filter(
            models.Provincia.id_ccaa == ccaa.id,
            models.MunicipioVisitado.email_usuario == email
        ).scalar()
        
        porcentaje_ccaa = (visitados_ccaa / total_ccaa * 100) if total_ccaa > 0 else 0
        
        provincias_lista = []
        for prov in ccaa.provincias:
            total_prov = db.query(func.count(models.Municipio.codigo_ign)).filter(models.Municipio.id_provincia == prov.id).scalar()
            
            visitados_prov = db.query(func.count(models.Municipio.codigo_ign)).join(models.MunicipioVisitado).filter(
                models.Municipio.id_provincia == prov.id,
                models.MunicipioVisitado.email_usuario == email
            ).scalar()
            
            porcentaje_prov = (visitados_prov / total_prov * 100) if total_prov > 0 else 0
            
            provincias_lista.append({
                "id": prov.id,
                "nombre": prov.nombre,
                "visitados": visitados_prov,
                "total": total_prov,
                "porcentaje": round(porcentaje_prov, 2)
            })
            
        resultado_panel.append({
            "id": ccaa.id,
            "nombre": ccaa.nombre,
            "visitados": visitados_ccaa,
            "total": total_ccaa,
            "porcentaje": round(porcentaje_ccaa, 2),
            "provincias": provincias_lista
        })
        
    # Devolvemos el HTML pasando el usuario y los datos calculados
    return templates.TemplateResponse(request, "panel.html", {"request": request, "usuario": usuario_actual, "datos": resultado_panel}) # type: ignore

@app.get("/panel/provincia/{id_provincia}")
@app.get("/panel/provincia/{id_provincia}", response_class=HTMLResponse)
def ver_detalle_provincia_html(id_provincia: str, request: Request, db: Session = Depends(get_db)):
    """
    Pinta la cuadrícula de municipios de una provincia.
    (TEMPORAL: Sin comprobación de token para pruebas visuales)
    """
    # TEMPORAL: Obtenemos a Pablo
    email = "pablo@ejemplo.com"
    
    # 1. Buscar info de la provincia
    provincia = db.query(models.Provincia).filter(models.Provincia.id == id_provincia).first()
    if not provincia:
        raise HTTPException(status_code=404, detail="Provincia no encontrada")

    # 2. La magia: LEFT OUTER JOIN
    resultados_db = db.query(
        models.Municipio, 
        models.MunicipioVisitado.codigo_ign_municipio
    ).outerjoin(
        models.MunicipioVisitado, 
        (models.Municipio.codigo_ign == models.MunicipioVisitado.codigo_ign_municipio) & 
        (models.MunicipioVisitado.email_usuario == email)
    ).filter(
        models.Municipio.id_provincia == id_provincia
    ).order_by(models.Municipio.nombre.asc()).all()

    # 3. Formatear la salida
    lista_municipios = []
    for municipio, codigo_visitado in resultados_db:
        lista_municipios.append({
            "codigo_ign": municipio.codigo_ign,
            "nombre": municipio.nombre,
            "visitado": True if codigo_visitado else False
        })

    # 4. Preparar datos para el HTML
    total = len(lista_municipios)
    visitados = sum(1 for m in lista_municipios if m["visitado"])

    datos_provincia = {
        "provincia_nombre": provincia.nombre,
        "total_municipios": total,
        "visitados": visitados,
        "municipios": lista_municipios
    }

    return templates.TemplateResponse(request, "municipios.html", {"request": request, "provincia": datos_provincia}) # type: ignore