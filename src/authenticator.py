"""
Módulo de autenticación para ARCA (ex-AFIP).
Maneja el login y la sesión del usuario.
"""

import logging
from playwright.sync_api import Page, BrowserContext
from src import config

logger = logging.getLogger(__name__)


class ARCAAuthenticator:
    """Maneja la autenticación en el sitio de ARCA"""

    def __init__(self, context: BrowserContext):
        self.context = context
        self.page = None

    def login(self) -> Page:
        """
        Realiza el login en ARCA usando las credenciales configuradas.

        Returns:
            Page: Página de Playwright autenticada

        Raises:
            Exception: Si el login falla
        """
        logger.info("Iniciando proceso de login en ARCA...")

        # Crear nueva página
        self.page = self.context.new_page()

        try:
            # Navegar a la página de login
            logger.info(f"Navegando a {config.ARCA_LOGIN_URL}")
            self.page.goto(config.ARCA_LOGIN_URL, timeout=config.BROWSER_TIMEOUT)

            # Esperar a que cargue el formulario de login
            logger.info("Esperando formulario de login...")
            self.page.wait_for_load_state("networkidle")

            # Esperar un momento adicional para que el modal se muestre completamente
            import time
            time.sleep(2)

            # Tomar screenshot del estado inicial para debugging
            logger.info("Capturando estado inicial del formulario...")
            initial_screenshot = config.LOGS_DIR / 'login_initial.png'
            self.page.screenshot(path=str(initial_screenshot))
            logger.info(f"Screenshot inicial guardado en: {initial_screenshot}")

            # Ingresar CUIT - buscar cualquier input de tipo texto visible
            logger.info(f"Buscando campo de CUIT...")
            # Intentar múltiples selectores posibles
            cuit_selectors = [
                'input[id*="username"]',
                'input[name*="username"]',
                'input[type="text"]',
                'input[placeholder*="CUIT"]',
                'input[placeholder*="usuario"]',
                '#F1\\:username',
                'input.form-control'
            ]

            cuit_input = None
            for selector in cuit_selectors:
                try:
                    locator = self.page.locator(selector).first
                    if locator.is_visible(timeout=2000):
                        cuit_input = locator
                        logger.info(f"Campo CUIT encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not cuit_input:
                raise Exception("No se pudo encontrar el campo de CUIT")

            logger.info(f"Ingresando CUIT: {config.ARCA_CUIT}")
            cuit_input.click()
            cuit_input.fill(config.ARCA_CUIT)

            # Tomar screenshot después de llenar CUIT
            logger.info("Capturando estado después de ingresar CUIT...")
            after_cuit_screenshot = config.LOGS_DIR / 'login_after_cuit.png'
            self.page.screenshot(path=str(after_cuit_screenshot))
            logger.info(f"Screenshot guardado en: {after_cuit_screenshot}")

            # PASO 1: Buscar el primer botón "Ingresar" para enviar el CUIT
            logger.info("Buscando primer botón Ingresar (para enviar CUIT)...")
            first_button_selectors = [
                'button:has-text("Ingresar")',
                'input[type="submit"]',
                'button[type="submit"]',
                'input[value*="Ingresar"]',
                'button.btn-primary',
                'button.btn'
            ]

            first_button = None
            for selector in first_button_selectors:
                try:
                    locator = self.page.locator(selector).first
                    if locator.is_visible(timeout=2000):
                        first_button = locator
                        logger.info(f"Primer botón Ingresar encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not first_button:
                raise Exception("No se pudo encontrar el primer botón Ingresar")

            logger.info("Haciendo clic en primer botón Ingresar...")
            first_button.click()

            # Esperar a que cargue la siguiente pantalla con el campo de password
            logger.info("Esperando que aparezca el campo de password...")
            time.sleep(3)  # Esperar un poco más para que cargue
            self.page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)

            # Tomar screenshot de la pantalla de password
            password_screen_screenshot = config.LOGS_DIR / 'login_password_screen.png'
            self.page.screenshot(path=str(password_screen_screenshot))
            logger.info(f"Screenshot de pantalla password guardado en: {password_screen_screenshot}")

            # PASO 2: Ahora buscar el campo de password
            logger.info("Buscando campo de password...")
            password_selectors = [
                'input[type="password"]',
                'input[id*="password"]',
                'input[name*="password"]',
                '#F1\\:password',
                'input[placeholder*="clave"]',
                'input[placeholder*="contraseña"]',
                'input[placeholder*="Clave"]'
            ]

            password_input = None
            for selector in password_selectors:
                try:
                    locator = self.page.locator(selector).first
                    if locator.is_visible(timeout=5000):
                        password_input = locator
                        logger.info(f"Campo password encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not password_input:
                raise Exception("No se pudo encontrar el campo de password después de enviar el CUIT")

            logger.info("Ingresando password...")
            password_input.click()
            password_input.fill(config.ARCA_PASSWORD)

            # Tomar screenshot antes de hacer clic final
            logger.info("Capturando estado antes de hacer clic final...")
            before_click_screenshot = config.LOGS_DIR / 'login_before_final_click.png'
            self.page.screenshot(path=str(before_click_screenshot))
            logger.info(f"Screenshot guardado en: {before_click_screenshot}")

            # PASO 3: Buscar el botón final de login
            logger.info("Buscando botón final de login...")
            final_button_selectors = [
                'button:has-text("Ingresar")',
                'input[type="submit"]',
                'button[type="submit"]',
                'input[value*="Ingresar"]',
                'button:has-text("Entrar")',
                'button.btn-primary',
                'button.btn'
            ]

            final_button = None
            for selector in final_button_selectors:
                try:
                    locator = self.page.locator(selector).first
                    if locator.is_visible(timeout=2000):
                        final_button = locator
                        logger.info(f"Botón final de login encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not final_button:
                raise Exception("No se pudo encontrar el botón final de login")

            logger.info("Haciendo clic en botón final de login...")
            final_button.click()

            # Esperar a que complete la autenticación
            logger.info("Esperando respuesta de autenticación...")
            self.page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)

            # Esperar un poco más para asegurar que la página cargó
            time.sleep(2)

            # Tomar screenshot después del login
            after_login_screenshot = config.LOGS_DIR / 'login_after.png'
            self.page.screenshot(path=str(after_login_screenshot))
            logger.info(f"Screenshot post-login guardado en: {after_login_screenshot}")

            # Verificar si el login fue exitoso comprobando que salimos de la página de login
            current_url = self.page.url
            logger.info(f"URL actual después del login: {current_url}")
            if config.ARCA_LOGIN_URL in current_url:
                raise Exception("Login fallido: la página no redirigió fuera del formulario de login")

            logger.info("Login exitoso!")
            return self.page

        except Exception as e:
            logger.error(f"Error durante el login: {str(e)}")
            if self.page:
                # Guardar screenshot para debugging
                screenshot_path = config.LOGS_DIR / 'login_error.png'
                self.page.screenshot(path=str(screenshot_path))
                logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def navigate_to_iva(self) -> Page:
        """
        Navega al Portal IVA a través de los links del portal de servicios.

        Flujo:
        1. Hace clic en "Ver todos" → va a mis-servicios
        2. Hace clic en "PORTAL IVA" → captura la nueva pestaña
        3. Devuelve la nueva pestaña con el Portal IVA abierto

        Returns:
            Page: Nueva pestaña con el Portal IVA

        Raises:
            Exception: Si no se puede acceder al Portal IVA
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        import time

        try:
            # PASO 1: Hacer clic en "Ver todos" para ir al listado completo de servicios
            logger.info("Buscando link 'Ver todos' para ir a mis-servicios...")
            ver_todos = self.page.locator('a[href="/portal/app/mis-servicios"]').first
            ver_todos.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)
            ver_todos.click()
            self.page.wait_for_load_state("networkidle")
            time.sleep(2)

            screenshot = config.LOGS_DIR / 'mis_servicios.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot mis-servicios guardado en: {screenshot}")
            logger.info(f"URL actual: {self.page.url}")

            # PASO 2: Hacer clic en "PORTAL IVA" — se abre en nueva pestaña
            logger.info("Buscando 'PORTAL IVA'...")
            portal_iva = self.page.locator('h3:has-text("PORTAL IVA")').first
            portal_iva.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)

            with self.page.context.expect_page() as new_page_info:
                portal_iva.click()
                logger.info("Clic en 'PORTAL IVA' realizado")

            new_page = new_page_info.value

            # Registrar URL inmediatamente (antes de cualquier espera)
            logger.info(f"[IVA] URL inicial capturada: {new_page.url}")

            # Seguir cada cambio de URL para ver la secuencia completa
            new_page.on(
                "framenavigated",
                lambda frame: logger.info(f"[IVA NAVIGATE] {frame.url}") if frame == new_page.main_frame else None
            )
            new_page.on("pageerror", lambda err: logger.error(f"[IVA JS ERROR] {err}"))
            new_page.on("requestfailed", lambda req: logger.error(f"[IVA REQUEST FAILED] {req.method} {req.url} — {req.failure}"))

            # Esperar a que la SPA complete su inicialización y llegue a #/init
            logger.info("Esperando que la SPA navegue a #/init...")
            new_page.wait_for_url("**/iva/#/init*", timeout=config.DOWNLOAD_TIMEOUT)
            logger.info(f"SPA inicializada. URL: {new_page.url}")

            iva_screenshot = config.LOGS_DIR / 'iva_inicio.png'
            new_page.screenshot(path=str(iva_screenshot))
            logger.info(f"Screenshot Portal IVA guardado en: {iva_screenshot}")

            self.page = new_page
            return new_page

        except Exception as e:
            logger.error(f"Error al navegar a Portal IVA: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'navigation_error.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def get_iva_cookies(self) -> dict:
        """
        Extrae las cookies del Portal IVA del contexto del browser.
        Se llama después de navigate_to_iva() para obtener el JSESSIONID
        que usa IVAApiClient para las llamadas REST.

        Returns:
            dict: Cookies del dominio siapweb.cloud.afip.gob.ar
        """
        all_cookies = self.page.context.cookies()
        iva_cookies = {
            c["name"]: c["value"]
            for c in all_cookies
            if "siapweb" in c.get("domain", "")
        }
        logger.info(f"Cookies IVA extraídas: {list(iva_cookies.keys())}")
        return iva_cookies

    def sync_iva_post_relacion(self) -> Page:
        """
        Después de seleccionar el representado vía API REST, recarga el Portal IVA
        en Playwright para sincronizar el estado de la SPA.

        Returns:
            Page: Página sincronizada en #/init
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        import time

        try:
            logger.info("Sincronizando Portal IVA tras cambio de representado...")
            self.page.goto(config.ARCA_IVA_URL, timeout=config.BROWSER_TIMEOUT)
            self.page.wait_for_url("**/iva/#/init*", timeout=config.DOWNLOAD_TIMEOUT)
            time.sleep(1)

            screenshot = config.LOGS_DIR / 'representado_activo.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot guardado en: {screenshot}")
            logger.info(f"URL sincronizada: {self.page.url}")

            return self.page

        except Exception as e:
            logger.error(f"Error al sincronizar Portal IVA: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'sync_error.png'
            self.page.screenshot(path=str(screenshot_path))
            raise

    def ingresar_nueva_declaracion(self) -> Page:
        """
        En el Portal IVA, hace clic en el botón "Ingresar" de Nueva declaración jurada.

        Returns:
            Page: Página de Playwright luego del clic

        Raises:
            Exception: Si no se encuentra el botón
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        try:
            logger.info("Esperando botón 'Ingresar' de Nueva declaración jurada...")
            boton = self.page.locator('button[aria-label*="nueva.declaracion"]').first
            boton.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)

            logger.info("Haciendo clic en 'Ingresar'...")
            boton.click()

            logger.info("Esperando que carguen los períodos disponibles...")
            self.page.wait_for_selector(
                'text="Buscando períodos disponibles ..."',
                state="hidden",
                timeout=config.DOWNLOAD_TIMEOUT
            )
            logger.info("Períodos cargados.")

            screenshot = config.LOGS_DIR / 'nueva_declaracion.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot guardado en: {screenshot}")
            logger.info(f"URL actual: {self.page.url}")

            return self.page

        except Exception as e:
            logger.error(f"Error al ingresar a Nueva declaración jurada: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'nueva_declaracion_error.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def ingresar_periodo(self) -> Page:
        """
        En la pantalla de Nueva declaración jurada, confirma el período seleccionado
        haciendo clic en "Ingresar" (aria-label validar.periodo).
        El resultado es el panel "Registración y declaración" con el botón home.liva.

        Returns:
            Page: Página de Playwright con el panel de opciones de declaración

        Raises:
            Exception: Si no se encuentra el botón o no aparece el panel siguiente
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        try:
            logger.info("Esperando botón 'Ingresar' para validar período...")
            boton = self.page.locator('button[aria-label*="validar.periodo"]').first
            boton.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)

            logger.info("Haciendo clic en 'Ingresar' (validar período)...")
            boton.click()

            # Esperar a que aparezca el panel con el botón de Registración y declaración
            logger.info("Esperando panel 'Registración y declaración'...")
            self.page.wait_for_selector(
                'button[aria-label*="home.liva"]',
                state="visible",
                timeout=config.BROWSER_TIMEOUT
            )

            screenshot = config.LOGS_DIR / 'panel_declaracion.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot guardado en: {screenshot}")
            logger.info(f"URL actual: {self.page.url}")

            return self.page

        except Exception as e:
            logger.error(f"Error al validar período: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'ingresar_periodo_error.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def ingresar_registro_declaracion(self) -> Page:
        """
        En el panel de opciones de declaración, hace clic en "Ingresar" de
        "Registración y declaración" (aria-label home.liva).
        Navega de siapweb.cloud.afip.gob.ar al Libro IVA en liva.afip.gob.ar.

        Returns:
            Page: Página de Playwright en liva.afip.gob.ar/liva/jsp/verCompras.do

        Raises:
            Exception: Si no se encuentra el botón o falla la navegación
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        try:
            logger.info("Esperando botón 'Ingresar' de Registración y declaración...")
            boton = self.page.locator('button[aria-label*="home.liva"]').first
            boton.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)

            logger.info("Haciendo clic en 'Ingresar' (navegará a liva.afip.gob.ar)...")
            boton.click()
            self.page.wait_for_url("**/liva/jsp/**", timeout=config.DOWNLOAD_TIMEOUT)
            self.page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)

            screenshot = config.LOGS_DIR / 'libro_compras.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot guardado en: {screenshot}")
            logger.info(f"URL actual: {self.page.url}")

            return self.page

        except Exception as e:
            logger.error(f"Error al ingresar a Registración y declaración: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'ingresar_registro_error.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def navegar_libro_compras(self) -> Page:
        """
        En la página inicial de liva.afip.gob.ar, hace clic en el panel
        "Libro Compras" para ir a verCompras.do?t=21 con la tabla de comprobantes.

        Returns:
            Page: Página de Playwright en verCompras.do?t=21

        Raises:
            Exception: Si no se encuentra el panel o falla la navegación
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        try:
            logger.info("Esperando panel 'Libro Compras'...")
            panel = self.page.locator('#btnLibroCompras').first
            panel.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)

            logger.info("Haciendo clic en 'Libro Compras'...")
            panel.click()
            self.page.wait_for_url("**/verCompras.do*", timeout=config.BROWSER_TIMEOUT)
            self.page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)

            screenshot = config.LOGS_DIR / 'ver_compras.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot guardado en: {screenshot}")
            logger.info(f"URL actual: {self.page.url}")

            return self.page

        except Exception as e:
            logger.error(f"Error al navegar a Libro Compras: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'libro_compras_error.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def importar_desde_arca(self) -> Page:
        """
        En la página del Libro Compras, importa comprobantes desde ARCA antes de la descarga:
        1. Abre el dropdown "Importar"
        2. Hace clic en "Importar desde ARCA..."
        3. Selecciona "Reemplazar el comprobante previamente incluído"
        4. Hace clic en "Importar" y espera que finalice
        5. Hace clic en "Actualizar"
        6. Cierra el modal manualmente

        Returns:
            Page: Página de Playwright tras cerrar el modal

        Raises:
            Exception: Si algún paso falla
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        import time

        try:
            # PASO 1: Abrir el dropdown "Importar"
            logger.info("Haciendo clic en el menú desplegable 'Importar'...")
            dropdown_btn = self.page.locator('#btnDropdownImportar')
            dropdown_btn.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)
            dropdown_btn.click()

            # PASO 2: Hacer clic en "Importar desde ARCA..." dentro del dropdown
            logger.info("Haciendo clic en 'Importar desde ARCA'...")
            lnk = self.page.locator('#lnkImportarAFIP')
            lnk.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)
            lnk.click()

            # Esperar que el modal esté visible
            logger.info("Esperando apertura del modal de importación...")
            self.page.wait_for_selector('#contenidoAFIP', state="visible", timeout=config.BROWSER_TIMEOUT)
            time.sleep(1)

            # PASO 3: Seleccionar "Reemplazar el comprobante previamente incluído" (valor 2)
            logger.info("Seleccionando modo 'Reemplazar'...")
            self.page.select_option('#modoImportacionAFIP', '2')

            screenshot = config.LOGS_DIR / 'importar_modal.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot modal guardado en: {screenshot}")

            # PASO 4: Hacer clic en "Importar"
            logger.info("Iniciando importación...")
            btn_importar = self.page.locator('#btnImportarAFIPImportar')
            btn_importar.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)
            btn_importar.click()

            # PASO 5: Esperar que aparezca el botón "Actualizar" (oculto hasta que termina la importación)
            logger.info("Esperando que finalice la importación...")
            btn_actualizar = self.page.locator('#btnTareasActualizar button')
            btn_actualizar.wait_for(state="visible", timeout=config.DOWNLOAD_TIMEOUT)
            logger.info("Importación finalizada, botón 'Actualizar' visible")

            screenshot = config.LOGS_DIR / 'importar_progreso.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot progreso guardado en: {screenshot}")

            # PASO 6: Hacer clic en "Actualizar"
            logger.info("Haciendo clic en 'Actualizar'...")
            btn_actualizar.click()
            self.page.wait_for_load_state("networkidle", timeout=config.BROWSER_TIMEOUT)
            logger.info("Actualización completada")

            # PASO 7: Cerrar el modal con el botón "Cerrar"
            logger.info("Cerrando modal...")
            close_btn = self.page.locator('#btnTareasCerrar button')
            close_btn.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)
            close_btn.click()
            self.page.wait_for_selector('.modal-backdrop', state="hidden", timeout=config.BROWSER_TIMEOUT)
            logger.info("Modal cerrado")

            screenshot = config.LOGS_DIR / 'importar_completado.png'
            self.page.screenshot(path=str(screenshot))
            logger.info(f"Screenshot final guardado en: {screenshot}")

            return self.page

        except Exception as e:
            logger.error(f"Error durante la importación desde ARCA: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'importar_error.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def descargar_csv_libro_compras(self, filepath) -> "Path":
        """
        En la página del Libro Compras (liva.afip.gob.ar), hace clic en el
        botón CSV y guarda el archivo descargado en la ruta indicada.

        Args:
            filepath: Path donde guardar el CSV descargado

        Returns:
            Path: Ruta del archivo guardado

        Raises:
            Exception: Si no se encuentra el botón CSV o falla la descarga
        """
        if not self.page:
            raise Exception("Debe realizar login primero")

        import zipfile
        from pathlib import Path as _Path

        try:
            logger.info("Buscando botón de descarga CSV...")
            csv_boton = self.page.locator('button[title="Exportar como CSV"]').first
            csv_boton.wait_for(state="visible", timeout=config.BROWSER_TIMEOUT)

            logger.info("Iniciando descarga...")
            with self.page.expect_download(timeout=config.DOWNLOAD_TIMEOUT) as download_info:
                csv_boton.click()

            download = download_info.value
            save_path = _Path(filepath)
            zip_path = save_path.with_suffix('.zip')
            download.save_as(str(zip_path))
            logger.info(f"Archivo descargado en: {zip_path}")

            # Extraer el CSV del zip
            with zipfile.ZipFile(zip_path) as zf:
                nombres = zf.namelist()
                logger.info(f"Contenido del zip: {nombres}")
                csv_nombre = next(
                    (n for n in nombres if n.lower().endswith('.csv')),
                    nombres[0]
                )
                with zf.open(csv_nombre) as src, open(str(save_path), 'wb') as dst:
                    dst.write(src.read())

            zip_path.unlink()
            logger.info(f"CSV extraído en: {save_path}")
            return save_path

        except Exception as e:
            logger.error(f"Error al descargar CSV: {str(e)}")
            screenshot_path = config.LOGS_DIR / 'csv_download_error.png'
            self.page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot guardado en: {screenshot_path}")
            raise

    def close(self) -> None:
        """Cierra la página del navegador"""
        if self.page:
            try:
                self.page.close()
                logger.info("Página cerrada")
            except Exception as e:
                # Ignorar errores si el event loop ya está cerrado
                logger.debug(f"Error al cerrar página (puede ser ignorado): {str(e)}")
