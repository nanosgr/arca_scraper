"""
Módulo de descarga de comprobantes desde ARCA.
Maneja la descarga de archivos CSV de comprobantes recibidos.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page, Download
from src import config

logger = logging.getLogger(__name__)


class ComprobantesDownloader:
    """Maneja la descarga de comprobantes desde ARCA"""

    def __init__(self, page: Page):
        self.page = page

    def download_comprobantes_recibidos(self, fecha_desde: str = None, fecha_hasta: str = None) -> Path:
        """
        Descarga los comprobantes recibidos en formato CSV.

        Args:
            fecha_desde: Fecha de inicio en formato DD/MM/YYYY (opcional)
            fecha_hasta: Fecha de fin en formato DD/MM/YYYY (opcional)

        Returns:
            Path: Ruta del archivo CSV descargado

        Raises:
            Exception: Si la descarga falla
        """
        logger.info("Iniciando descarga de comprobantes recibidos...")

        try:
            # Navegar a la página de comprobantes recibidos
            logger.info(f"Navegando a {config.ARCA_COMPROBANTES_RECIBIDOS_URL}")
            self.page.goto(config.ARCA_COMPROBANTES_RECIBIDOS_URL, timeout=config.BROWSER_TIMEOUT)
            self.page.wait_for_load_state("networkidle")

            # Si se especifican fechas, llenar los campos de fecha
            if fecha_desde:
                logger.info(f"Configurando fecha desde: {fecha_desde}")
                # NOTA: Ajustar selectores según la estructura real del sitio
                fecha_desde_input = self.page.locator('input[name*="fechaDesde"], input[id*="fechaDesde"]').first
                fecha_desde_input.fill(fecha_desde)

            if fecha_hasta:
                logger.info(f"Configurando fecha hasta: {fecha_hasta}")
                fecha_hasta_input = self.page.locator('input[name*="fechaHasta"], input[id*="fechaHasta"]').first
                fecha_hasta_input.fill(fecha_hasta)

            # Buscar el botón de descarga CSV
            # Puede ser un botón con texto "Exportar", "Descargar CSV", o similar
            logger.info("Buscando botón de descarga CSV...")

            # Configurar el handler de descarga antes de hacer clic
            with self.page.expect_download(timeout=config.DOWNLOAD_TIMEOUT) as download_info:
                # Intentar varios selectores comunes para el botón de descarga
                download_button = self.page.locator(
                    'button:has-text("CSV"), '
                    'a:has-text("CSV"), '
                    'input[value*="CSV"], '
                    'button:has-text("Exportar"), '
                    'a:has-text("Exportar"), '
                    'button:has-text("Descargar")'
                ).first

                logger.info("Haciendo clic en botón de descarga...")
                download_button.click()

            # Obtener el objeto de descarga
            download: Download = download_info.value

            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprobantes_recibidos_{timestamp}.csv"
            destination_path = config.DATA_DIR / filename

            # Guardar el archivo
            logger.info(f"Guardando archivo en: {destination_path}")
            download.save_as(destination_path)

            # Verificar que el archivo se descargó correctamente
            if not destination_path.exists():
                raise Exception("El archivo no se descargó correctamente")

            file_size = destination_path.stat().st_size
            logger.info(f"Descarga exitosa! Archivo: {filename} ({file_size} bytes)")

            return destination_path

        except Exception as e:
            logger.error(f"Error durante la descarga: {str(e)}")
            screenshot_path = config.LOGS_DIR / f'download_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def download_with_filters(self, filtros: dict) -> Path:
        """
        Descarga comprobantes con filtros personalizados.

        Args:
            filtros: Diccionario con filtros como:
                {
                    'fecha_desde': 'DD/MM/YYYY',
                    'fecha_hasta': 'DD/MM/YYYY',
                    'tipo_comprobante': 'Factura A',
                    'emisor': 'CUIT o nombre',
                    # ... otros filtros según disponibilidad en ARCA
                }

        Returns:
            Path: Ruta del archivo CSV descargado
        """
        logger.info(f"Aplicando filtros: {filtros}")

        try:
            # Navegar a comprobantes recibidos
            self.page.goto(config.ARCA_COMPROBANTES_RECIBIDOS_URL, timeout=config.BROWSER_TIMEOUT)
            self.page.wait_for_load_state("networkidle")

            # Aplicar cada filtro
            for campo, valor in filtros.items():
                logger.info(f"Aplicando filtro {campo}: {valor}")
                # NOTA: Los selectores específicos dependerán del formulario real de ARCA
                # Este es un ejemplo genérico que debe ajustarse
                input_field = self.page.locator(f'input[name*="{campo}"], input[id*="{campo}"], select[name*="{campo}"]').first

                if input_field.count() > 0:
                    if input_field.evaluate("el => el.tagName") == "SELECT":
                        input_field.select_option(valor)
                    else:
                        input_field.fill(valor)
                else:
                    logger.warning(f"No se encontró el campo para el filtro: {campo}")

            # Buscar comprobantes con los filtros aplicados
            search_button = self.page.locator('button:has-text("Buscar"), input[type="submit"][value*="Buscar"]').first
            if search_button.count() > 0:
                logger.info("Ejecutando búsqueda con filtros...")
                search_button.click()
                self.page.wait_for_load_state("networkidle")

            # Ahora descargar el CSV
            return self.download_comprobantes_recibidos()

        except Exception as e:
            logger.error(f"Error aplicando filtros: {str(e)}")
            raise
