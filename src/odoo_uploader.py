"""
Sube el CSV del Libro de Compras al endpoint HTTP del módulo
l10n_ar_import_arca_excel (Odoo), para que se importe automáticamente sin
intervención manual. El resumen de la importación (facturas nuevas,
duplicadas, con error) lo envía Odoo por mail; acá solo se deja constancia
en el log de si la subida en sí funcionó o no.
"""

import logging
from pathlib import Path

import requests

from src import config

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(config.ODOO_UPLOAD_URL and config.ODOO_API_TOKEN and config.ODOO_COMPANY_ID)


def upload_libro_compras(csv_path: Path, timeout: int = 180) -> dict:
    """
    Sube 'csv_path' al endpoint de importación de Odoo.

    Lanza excepción si la petición HTTP en sí falla (timeout, conexión,
    status >= 400). Un fallo de negocio dentro de Odoo (ej. archivo con
    columnas inesperadas) vuelve como success=False en el JSON, sin excepción,
    ya que la subida sí se completó.
    """
    if not is_configured():
        raise RuntimeError(
            "Integración con Odoo no configurada: definí ODOO_UPLOAD_URL, "
            "ODOO_API_TOKEN y ODOO_COMPANY_ID en el archivo .env"
        )

    logger.info(f"Subiendo '{csv_path.name}' a Odoo ({config.ODOO_UPLOAD_URL})...")
    with open(csv_path, 'rb') as f:
        response = requests.post(
            config.ODOO_UPLOAD_URL,
            data={'token': config.ODOO_API_TOKEN, 'company_id': config.ODOO_COMPANY_ID},
            files={'file': (csv_path.name, f, 'text/csv')},
            timeout=timeout,
        )
    response.raise_for_status()
    result = response.json()

    if result.get('success'):
        summary = result.get('summary', {})
        logger.info(
            "Importación en Odoo OK: %s nuevas, %s ya existentes, %s con error (revisar mail)",
            summary.get('imported_count'), summary.get('duplicates_count'), summary.get('failed_count'))
    else:
        logger.error(f"Odoo respondió con error al importar: {result.get('error')}")

    return result
