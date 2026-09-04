"""
Configuración del proyecto ARCA Scraper.
Carga las credenciales desde el archivo .env
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Credenciales ARCA (cuenta gestora/apoderada, común a todas las empresas representadas)
ARCA_CUIT = os.getenv('ARCA_CUIT')
ARCA_PASSWORD = os.getenv('ARCA_PASSWORD')

# Validar que las credenciales estén configuradas
if not ARCA_CUIT or not ARCA_PASSWORD:
    raise ValueError(
        "Error: Las credenciales no están configuradas.\n"
        "Por favor, crea un archivo .env basándote en .env.example "
        "y completa ARCA_CUIT y ARCA_PASSWORD"
    )

# URLs de ARCA
ARCA_LOGIN_URL = "https://auth.afip.gob.ar/contribuyente_/login.xhtml"
ARCA_IVA_URL = "https://siapweb.cloud.afip.gob.ar/iva/"

# Directorios del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
EMPRESAS_FILE = PROJECT_ROOT / 'config' / 'empresas.json'

# Configuración de Playwright
BROWSER_HEADLESS = os.getenv('BROWSER_HEADLESS', 'false').lower() == 'true'
BROWSER_TIMEOUT = 30000  # 30 segundos
DOWNLOAD_TIMEOUT = 60000  # 60 segundos para descargas
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Integración con Odoo: subida automática del CSV descargado al endpoint del
# módulo l10n_ar_import_arca_excel (importa el Libro de Compras sin
# intervención manual). Opcional: si no están las 2 variables, se omite el
# paso de subida y el scraper se comporta como hasta ahora (solo descarga).
# ODOO_UPLOAD_URL apunta al ambiente elegido (producción o staging), a
# criterio de quien despliega este .env. El company_id (distinto por cada
# empresa representada) se define en config/empresas.json, no acá.
ODOO_UPLOAD_URL = os.getenv('ODOO_UPLOAD_URL')  # ej: https://aerotec.odoo.com/l10n_ar_arca_import/upload
ODOO_API_TOKEN = os.getenv('ODOO_API_TOKEN')


def cargar_empresas() -> list:
    """
    Carga la lista de empresas representadas desde config/empresas.json.
    Cada entrada requiere 'cuit', 'nombre' y 'odoo_company_id'.
    """
    if not EMPRESAS_FILE.exists():
        raise ValueError(
            f"Error: no se encontró {EMPRESAS_FILE}. "
            "Creá el archivo con al menos una empresa representada "
            "(ver README.md)."
        )

    with open(EMPRESAS_FILE, encoding='utf-8') as f:
        empresas = json.load(f)

    if not isinstance(empresas, list) or not empresas:
        raise ValueError(f"Error: {EMPRESAS_FILE} debe contener una lista no vacía de empresas.")

    campos_requeridos = {'cuit', 'nombre', 'odoo_company_id'}
    for i, empresa in enumerate(empresas):
        faltantes = campos_requeridos - empresa.keys()
        if faltantes:
            raise ValueError(
                f"Error: la empresa en la posición {i} de {EMPRESAS_FILE} "
                f"no tiene los campos {sorted(faltantes)}"
            )

    return empresas


# Empresas representadas a procesar en cada corrida
EMPRESAS = cargar_empresas()
