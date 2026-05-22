"""
Configuración del proyecto ARCA Scraper.
Carga las credenciales desde el archivo .env
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Credenciales ARCA
ARCA_CUIT = os.getenv('ARCA_CUIT')
ARCA_PASSWORD = os.getenv('ARCA_PASSWORD')

# Representado activo
ARCA_REPRESENTADO_CUIT = os.getenv('ARCA_REPRESENTADO_CUIT')
ARCA_REPRESENTADO_NOMBRE = os.getenv('ARCA_REPRESENTADO_NOMBRE')

# Validar que las credenciales estén configuradas
if not ARCA_CUIT or not ARCA_PASSWORD:
    raise ValueError(
        "Error: Las credenciales no están configuradas.\n"
        "Por favor, crea un archivo .env basándote en .env.example "
        "y completa ARCA_CUIT y ARCA_PASSWORD"
    )

if not ARCA_REPRESENTADO_CUIT:
    raise ValueError(
        "Error: ARCA_REPRESENTADO_CUIT no está configurado en el archivo .env"
    )

# URLs de ARCA
ARCA_LOGIN_URL = "https://auth.afip.gob.ar/contribuyente_/login.xhtml"
ARCA_IVA_URL = "https://siapweb.cloud.afip.gob.ar/iva/"

# Directorios del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'

# Configuración de Playwright
BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true'
BROWSER_TIMEOUT = 30000  # 30 segundos
DOWNLOAD_TIMEOUT = 60000  # 60 segundos para descargas
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
