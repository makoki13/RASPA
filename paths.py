import os
from pathlib import Path

# BASE_DIR será la carpeta RASPA venga de donde venga
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = BASE_DIR / "templates"
GPX_TEMP_DIR = BASE_DIR / "gpx_temp"