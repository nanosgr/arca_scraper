"""
ARCA Scraper - Script principal
Automatiza la descarga de comprobantes recibidos desde ARCA (ex-AFIP)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

from src import config
from src.authenticator import ARCAAuthenticator
from src.iva_api import IVAApiClient


def setup_logging():
    """Configura el sistema de logging"""
    # Crear directorio de logs si no existe
    config.LOGS_DIR.mkdir(exist_ok=True)

    # Nombre del archivo de log con timestamp
    log_filename = config.LOGS_DIR / f"arca_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Configurar formato de log
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Configurar logging a archivo y consola
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def main():
    """Función principal del scraper"""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("Iniciando ARCA Scraper")
    logger.info("=" * 60)

    # Validar que el directorio de datos exista
    config.DATA_DIR.mkdir(exist_ok=True)

    browser = None
    context = None
    authenticator = None

    try:
        # Iniciar Playwright
        logger.info("Iniciando navegador con Playwright...")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                # channel="chrome",
                headless=config.BROWSER_HEADLESS,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context(user_agent=config.BROWSER_USER_AGENT)
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            logger.info(f"Navegador Chrome iniciado (headless={config.BROWSER_HEADLESS})")

            # Crear instancia del autenticador
            authenticator = ARCAAuthenticator(context)

            # Realizar login
            page = authenticator.login()

            # ── PLAYWRIGHT: navegar al Portal IVA ──────────────────────
            iva_page = authenticator.navigate_to_iva()

            # ── HÍBRIDO: extraer cookies y cambiar de representado vía API
            iva_cookies = authenticator.get_iva_cookies()
            iva_client = IVAApiClient(iva_cookies)

            logger.info(f"Seleccionando representado: {config.ARCA_REPRESENTADO_NOMBRE}")
            iva_client.seleccionar_representado(config.ARCA_REPRESENTADO_CUIT)

            # Sincronizar Playwright con el nuevo representado
            iva_page = authenticator.sync_iva_post_relacion()

            # ── PLAYWRIGHT: navegar al Libro Compras en liva.afip.gob.ar ──
            iva_page = authenticator.ingresar_nueva_declaracion()
            iva_page = authenticator.ingresar_periodo()
            iva_page = authenticator.ingresar_registro_declaracion()
            iva_page = authenticator.navegar_libro_compras()

            # ── PLAYWRIGHT: importar desde ARCA antes de descargar ────
            iva_page = authenticator.importar_desde_arca()

            # ── PLAYWRIGHT: descargar CSV del Libro Compras ────────────
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            cuit_limpio = config.ARCA_REPRESENTADO_CUIT.replace("-", "")
            csv_path = config.DATA_DIR / f"libro_compras_{cuit_limpio}_{timestamp}.csv"
            archivo = authenticator.descargar_csv_libro_compras(csv_path)

            logger.info("=" * 60)
            logger.info(f"Descarga completada: {archivo}")
            logger.info(f"Representado: {config.ARCA_REPRESENTADO_NOMBRE} ({config.ARCA_REPRESENTADO_CUIT})")
            logger.info("=" * 60)

            return 0

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Error durante la ejecución: {str(e)}")
        logger.error("=" * 60)
        return 1

    finally:
        # Cerrar recursos
        if authenticator:
            authenticator.close()
        if context:
            try:
                context.close()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
                logger.info("Navegador cerrado")
            except Exception as e:
                logger.debug(f"Error al cerrar navegador (puede ser ignorado): {str(e)}")


if __name__ == "__main__":
    sys.exit(main())
