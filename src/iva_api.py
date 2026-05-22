"""
Cliente de la API REST del Portal IVA (siapweb.cloud.afip.gob.ar).
Usa requests con el JSESSIONID extraído del browser Playwright.
"""

import logging
import requests
from src import config

logger = logging.getLogger(__name__)

BASE_URL = "https://siapweb.cloud.afip.gob.ar/iva/api"

HEADERS_BASE = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://siapweb.cloud.afip.gob.ar/iva/",
    "Origin": "https://siapweb.cloud.afip.gob.ar",
}


class IVAApiClient:
    """
    Cliente para la API REST del Portal IVA.
    Se instancia con las cookies del browser Playwright después de navegar al Portal IVA.
    """

    def __init__(self, cookies: dict):
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update(HEADERS_BASE)

    def seleccionar_representado(self, cuit: str) -> None:
        """
        Selecciona el representado vía API (reemplaza el flujo de changeRelation en Playwright).
        El CUIT puede tener guiones (30-69076240-0) o no (30690762400).
        """
        cuit_limpio = cuit.replace("-", "")
        url = f"{BASE_URL}/token/relacion/{cuit_limpio}"
        logger.info(f"Seleccionando representado vía API: CUIT {cuit_limpio}")
        resp = self.session.post(url, data="")
        resp.raise_for_status()
        logger.info(f"Representado seleccionado. HTTP {resp.status_code}")

    def get_estado_contribuyente(self) -> dict:
        """Estado del contribuyente activo."""
        resp = self.session.get(f"{BASE_URL}/app/contribuyente/estado")
        resp.raise_for_status()
        return resp.json() if resp.text.strip() else {}

    def get_caracterizacion_activa(self) -> dict:
        """Caracterización IVA activa del contribuyente."""
        resp = self.session.get(f"{BASE_URL}/app/caracterizacionActiva")
        resp.raise_for_status()
        return resp.json() if resp.text.strip() else {}
