import os
from dotenv import load_dotenv

# Carga las variables del archivo .env
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"