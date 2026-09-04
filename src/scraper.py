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
from src import odoo_uploader
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


def procesar_empresa(authenticator, iva_client, empresa, logger):
    """
    Selecciona 'empresa' como representado activo, descarga su Libro de
    Compras y, si Odoo está configurado, lo sube. No propaga excepciones:
    main() debe seguir con la próxima empresa si algo falla acá. Devuelve
    un dict con el resultado para el resumen final.
    """
    nombre = empresa['nombre']
    cuit = empresa['cuit']
    resultado = {'empresa': nombre, 'cuit': cuit, 'estado': 'error', 'detalle': None}

    try:
        logger.info(f"--- Procesando representado: {nombre} ({cuit}) ---")
        iva_client.seleccionar_representado(cuit)
        authenticator.sync_iva_post_relacion()
        authenticator.ingresar_nueva_declaracion()
        authenticator.ingresar_periodo()
        authenticator.ingresar_registro_declaracion()
        authenticator.navegar_libro_compras()
        authenticator.importar_desde_arca()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cuit_limpio = cuit.replace("-", "")
        csv_path = config.DATA_DIR / f"libro_compras_{cuit_limpio}_{timestamp}.csv"
        archivo = authenticator.descargar_csv_libro_compras(csv_path)
        logger.info(f"Descarga completada para {nombre}: {archivo}")
        resultado['estado'] = 'descargado'

        if odoo_uploader.is_configured():
            try:
                odoo_uploader.upload_libro_compras(Path(archivo), empresa['odoo_company_id'])
                resultado['estado'] = 'ok'
            except Exception as e:
                logger.error(f"Descarga OK para {nombre}, pero falló la subida a Odoo: {e}")
                resultado['estado'] = 'odoo_error'
                resultado['detalle'] = str(e)
        else:
            resultado['estado'] = 'ok'

    except Exception as e:
        logger.error(f"Error procesando {nombre} ({cuit}): {e}")
        resultado['detalle'] = str(e)

    return resultado


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

            empresas = config.EMPRESAS
            logger.info(f"Empresas a procesar: {len(empresas)}")
            if not odoo_uploader.is_configured():
                logger.info("Integración con Odoo no configurada (ODOO_UPLOAD_URL/ODOO_API_TOKEN); se omite la subida para todas las empresas.")

            resultados = [
                procesar_empresa(authenticator, iva_client, empresa, logger)
                for empresa in empresas
            ]

            # ── Resumen final ────────────────────────────────────────
            ok = [r for r in resultados if r['estado'] == 'ok']
            odoo_error = [r for r in resultados if r['estado'] in ('descargado', 'odoo_error')]
            fallidas = [r for r in resultados if r['estado'] == 'error']

            logger.info("=" * 60)
            logger.info(f"Resumen: {len(ok)}/{len(resultados)} empresas OK")
            for r in odoo_error:
                logger.warning(f"  - {r['empresa']} ({r['cuit']}): descarga OK, falló Odoo")
            for r in fallidas:
                logger.error(f"  - {r['empresa']} ({r['cuit']}): FALLÓ - {r['detalle']}")
            logger.info("=" * 60)

            if fallidas:
                return 1
            if odoo_error:
                return 2
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
