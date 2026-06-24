from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# Importamos la clave y el algoritmo del config que acabamos de crear
from server.config import SECRET_KEY, ALGORITHM

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_password(contrasena_plana: str, contrasena_hasheada: str) -> bool:
    return pwd_context.verify(contrasena_plana, contrasena_hasheada)

def obtener_hash_password(contrasena_plana: str) -> str:
    return pwd_context.hash(contrasena_plana)

def crear_token_acceso(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    # Usamos las variables importadas
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt