from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi import Response, Cookie, Form
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.templating import Jinja2Templates

# Importaciones de nuestros módulos
from server import models, database, security

# Arriba donde importas paths
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from paths import TEMPLATE_DIR

app = FastAPI(title="RASPA API", description="Race Across Spain - Backend")

# Este objeto de FastAPI es el que busca la pulsera (Token) en las cabeceras de las peticiones
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)

# Configurar Jinja2 para leer la carpeta de plantillas HTML
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

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

@app.get("/", response_class=HTMLResponse)
def pagina_ranking_html(request: Request, db: Session = Depends(get_db)):
    """Pinta la página web del ranking"""
    usuarios = db.query(models.Usuario).order_by(models.Usuario.puntos_totales.desc()).all()
    resultado = [{"nombre": u.nombre_publico, "puntos": u.puntos_totales} for u in usuarios]
    
    return templates.TemplateResponse(request, "ranking.html", {"request": request, "ranking": resultado}) # type: ignore


@app.get("/login", response_class=HTMLResponse)
def pagina_login(request: Request, error: str = None): # type: ignore
    """Muestra el formulario de login"""
    return templates.TemplateResponse(request, "login.html", {"request": request, "error": error}) # type: ignore


@app.post("/login")
def login_procesar(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Procesa el formulario, verifica la contraseña y redirige al panel con una Cookie.
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.email == form_data.username).first()
    hash_guardado = usuario.password_hash if usuario else None
    
    if not usuario or not hash_guardado or not security.verificar_password(form_data.password, hash_guardado): # type: ignore
        # Si falla, le pasamos el error a la página HTML
        raise HTTPException(status_code=303, detail="Correo o contraseña incorrectos", headers={"Location": "/login?error=Incorrectos"})
    
    # Si es correcto, generamos el token
    token_acceso = security.crear_token_acceso(data={"sub": usuario.email})
    
    # Creamos una redirección hacia el panel
    redirect = RedirectResponse(url="/panel", status_code=303)
    
    # ¡LA MAGIA! Metemos el token en una Cookie segura (httponly para que JavaScript no pueda robarla)
    redirect.set_cookie(key="access_token", value=token_acceso, httponly=True)
    
    return redirect


# ==========================================
# SISTEMA DE SEGURIDAD (El revisor de pulseras)
# ==========================================

def obtener_usuario_actual(
    request: Request, 
    access_token: str | None = Cookie(default=None), # Mira en las cookies
    bearer_token: str | None = Depends(oauth2_scheme), # Mira en la cabecera de /docs
    db: Session = Depends(get_db)
):
    # Usamos la cookie si existe, si no, usamos el token del swagger
    token_a_comprobar = access_token or bearer_token
    
    if not token_a_comprobar:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    try:
        payload = security.jwt.decode(token_a_comprobar, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except Exception:
        raise HTTPException(status_code=401, detail="Token caducado")
    
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return usuario

# ==========================================
# RUTAS PRIVADAS (Requieren pulsera válida)
# ==========================================

@app.get("/perfil")
def ver_mi_perfil(usuario_actual: models.Usuario = Depends(obtener_usuario_actual)):
    """ (Solo JSON para pruebas rápidas en /docs) """
    return {
        "mensaje": f"Hola {usuario_actual.nombre_publico}, has accedido a tu zona privada.",
        "tu_email_es": usuario_actual.email,
        "tus_puntos": usuario_actual.puntos_totales
    }


@app.get("/panel", response_class=HTMLResponse)
def ver_panel_html(request: Request, usuario_actual: models.Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)): # type: ignore
    """Pinta el panel de progreso del usuario con HTML."""
    email = usuario_actual.email
    resultado_panel = []

    ccaas = db.query(models.Ccaa).all()
    
    for ccaa in ccaas:
        # Total municipios en esta CCAA
        total_ccaa = db.query(func.count(models.Municipio.codigo_ign)).join(models.Provincia).filter(models.Provincia.id_ccaa == ccaa.id).scalar()
        
        # Municipios visitados por el usuario en esta CCAA
        visitados_ccaa = db.query(func.count(models.Municipio.codigo_ign)).join(models.Provincia).join(models.MunicipioVisitado).filter(
            models.Provincia.id_ccaa == ccaa.id,
            models.MunicipioVisitado.email_usuario == email
        ).scalar()
        
        porcentaje_ccaa = (visitados_ccaa / total_ccaa * 100) if total_ccaa > 0 else 0
        
        # Por cada CCAA, obtenemos sus Provincias
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
            
        # Montamos el bloque de la CCAA
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


@app.get("/panel/provincia/{id_provincia}", response_class=HTMLResponse)
def ver_detalle_provincia_html(id_provincia: str, request: Request, usuario_actual: models.Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)): # type: ignore
    """Pinta la cuadrícula de municipios de una provincia."""
    email = usuario_actual.email
    
    # 1. Buscar info de la provincia para ponerle nombre al título
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

    # 4. Calcular totales para la cabecera
    total = len(lista_municipios)
    visitados = sum(1 for m in lista_municipios if m["visitado"])

    datos_provincia = {
        "provincia_nombre": provincia.nombre,
        "total_municipios": total,
        "visitados": visitados,
        "municipios": lista_municipios
    }

    return templates.TemplateResponse(request, "municipios.html", {"request": request, "provincia": datos_provincia}) # type: ignore

# Cazador de errores: Si algo pide autenticación y falla, redirigimos al login
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.get("/perfil/password", response_class=HTMLResponse)
def formulario_password(request: Request, msg: str = None, usuario_actual: models.Usuario = Depends(obtener_usuario_actual)): # type: ignore
    """Muestra el formulario para cambiar la contraseña"""
    return templates.TemplateResponse(request, "cambiar_password.html", {"request": request, "msg": msg}) # type: ignore


@app.post("/perfil/password")
def procesar_cambio_password(
    request: Request, 
    old_password: str = Form(...), 
    new_password: str = Form(...), 
    new_password2: str = Form(...),
    usuario_actual: models.Usuario = Depends(obtener_usuario_actual), 
    db: Session = Depends(get_db)
):
    """Procesa el cambio de contraseña"""
    
    # 1. Comprobar que no estén vacías
    if not old_password or not new_password:
        return RedirectResponse(url="/perfil/password?msg=error_vacias", status_code=303)
        
    # 2. Comprobar que las dos nuevas coinciden
    if new_password != new_password2:
        return RedirectResponse(url="/perfil/password?msg=error_vacias", status_code=303)

    # 3. Verificar que la contraseña vieja es correcta
    hash_guardado = usuario_actual.password_hash
    if not security.verificar_password(old_password, hash_guardado): # type: ignore
        return RedirectResponse(url="/perfil/password?msg=error_vieja", status_code=303)

    # 4. Si todo es correcto, hasheamos la nueva y la guardamos
    nuevo_hash = security.obtener_hash_password(new_password)
    usuario_actual.password_hash = nuevo_hash
    db.commit()

    # 5. Redirigir al formulario con mensaje de éxito
    return RedirectResponse(url="/perfil/password?msg=actualizada", status_code=303)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401:
        return RedirectResponse(url="/login")
    # Si es otro error (ej. 404), dejamos que FastAPI lo maneje por defecto
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login")
    response.delete_cookie("access_token") # Borramos la pulsera
    return response