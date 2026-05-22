# ARCA Scraper

Herramienta para automatizar la descarga de comprobantes recibidos desde el sitio web de ARCA (ex-AFIP).

## Descripción

Este proyecto permite automatizar el proceso de login en el sitio de ARCA y descargar los comprobantes recibidos en formato CSV, eliminando la necesidad de hacerlo manualmente cada vez.

## Características

- Autenticación automática con CUIT y contraseña
- Descarga de comprobantes recibidos en formato CSV
- Soporte para filtros por fecha (opcional)
- Logging detallado de todas las operaciones
- Screenshots automáticos en caso de error para debugging
- Credenciales seguras mediante archivo .env

## Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## Instalación

### 1. Clonar o descargar el proyecto

```bash
cd arca_scraper
```

### 2. Crear entorno virtual (recomendado)

```bash
python -m venv venv

# En Linux/Mac:
source venv/bin/activate

# En Windows:
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar navegadores de Playwright

```bash
playwright install chromium
```

### 5. Instalar dependencias del sistema para Chromium

**Ubuntu 22.04 / Debian 11 y anteriores:**

```bash
playwright install-deps chromium
```

**Ubuntu 24.04 / Linux Mint 22 "Wilma" y derivados:**

El comando `playwright install-deps` falla en estas versiones porque varios paquetes fueron renombrados con sufijo `t64`. Instalar las dependencias manualmente:

```bash
sudo apt install -y \
  libnss3 \
  libnspr4 \
  libatk1.0-0t64 \
  libatk-bridge2.0-0t64 \
  libcups2t64 \
  libdrm2 \
  libxkbcommon0 \
  libxcomposite1 \
  libxdamage1 \
  libxfixes3 \
  libxrandr2 \
  libgbm1 \
  libasound2t64 \
  libpango-1.0-0 \
  libcairo2 \
  libatspi2.0-0t64 \
  libwayland-client0 \
  fonts-liberation \
  libx11-6 \
  libxcb1 \
  libxext6
```

### 6. Verificar instalación de Chromium headless

```bash
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); print('OK'); b.close(); p.stop()"
```

Si imprime `OK`, el entorno está listo para ejecutarse sin escritorio gráfico.

## Configuración

### 1. Configurar credenciales

Copia el archivo de ejemplo y completa tus credenciales:

```bash
cp .env.example .env
```

Edita el archivo `.env` y completa con tus datos reales:

```env
ARCA_CUIT=20123456789
ARCA_PASSWORD=tu_password_real
```

**IMPORTANTE:** El archivo `.env` contiene información sensible. Nunca lo subas a Git (ya está incluido en `.gitignore`).

### 2. Ajustar configuración (opcional)

Puedes modificar `src/config.py` para:

- Cambiar modo headless (con/sin interfaz gráfica del navegador)
- Ajustar timeouts
- Modificar rutas de directorios

## Uso

### Ejecución básica

Para descargar todos los comprobantes recibidos:

```bash
python -m src.scraper
```

### Ver el navegador en acción

Por defecto, el navegador se ejecuta en modo visible (`BROWSER_HEADLESS = False` en `config.py`). Esto te permite ver qué está haciendo el scraper. Para ejecutarlo sin interfaz gráfica (más rápido), cambia a `True`.

### Personalizar fechas

Para descargar comprobantes de un período específico, edita `src/scraper.py` en la función `main()`:

```python
# Descomentar y ajustar estas líneas:
fecha_desde = "01/01/2024"
fecha_hasta = "31/12/2024"
archivo_descargado = downloader.download_comprobantes_recibidos(fecha_desde, fecha_hasta)
```

## Estructura del Proyecto

```
arca_scraper/
├── src/
│   ├── __init__.py         # Inicialización del paquete
│   ├── config.py           # Configuración y credenciales
│   ├── authenticator.py    # Lógica de autenticación
│   ├── downloader.py       # Lógica de descarga
│   └── scraper.py          # Script principal
├── data/                   # Archivos CSV descargados
├── logs/                   # Logs de ejecución
├── tests/                  # Tests (futuro)
├── .env                    # Credenciales (NO commitear)
├── .env.example            # Plantilla de credenciales
├── .gitignore              # Archivos ignorados por Git
├── requirements.txt        # Dependencias Python
└── README.md               # Este archivo
```

## Archivos Generados

- **Comprobantes CSV**: Se guardan en `data/` con formato `comprobantes_recibidos_YYYYMMDD_HHMMSS.csv`
- **Logs**: Se guardan en `logs/` con formato `arca_scraper_YYYYMMDD_HHMMSS.log`
- **Screenshots de error**: Si algo falla, se guardan screenshots en `logs/` para debugging

## Solución de Problemas

### Error: "Las credenciales no están configuradas"

Asegúrate de haber creado el archivo `.env` con tus credenciales correctas.

### Error durante el login

1. Verifica que tus credenciales sean correctas
2. Revisa el screenshot generado en `logs/login_error.png`
3. Es posible que los selectores del formulario hayan cambiado. Revisa `src/authenticator.py`

### El navegador no abre

1. Asegúrate de haber ejecutado `playwright install chromium`
2. Verifica que no haya problemas con tu instalación de Python

### Los selectores no funcionan

El sitio de ARCA puede cambiar su estructura HTML. Si esto sucede:

1. Ejecuta el scraper en modo visible (headless=False)
2. Inspecciona los elementos con las DevTools del navegador
3. Actualiza los selectores en `src/authenticator.py` y `src/downloader.py`

## Ejecución en servidor Linux sin escritorio gráfico

El scraper puede correr en una máquina sin entorno gráfico (consola bash pura, servidor, VM headless) siempre que Chromium esté en modo headless.

### Configurar modo headless

En el archivo `.env`, agregar o verificar:

```env
BROWSER_HEADLESS=true
```

Alternativamente, editar `src/config.py`:

```python
BROWSER_HEADLESS = True
```

Con esta configuración el navegador corre completamente en memoria, sin necesidad de pantalla ni servidor X.

---

## Automatización con Cron

### Configuración básica

Abrir el crontab del usuario:

```bash
crontab -e
```

Agregar una línea con la frecuencia deseada. Ejemplos:

```cron
# Todos los días a las 8:00 AM
0 8 * * * /home/usuario/arca_scraper/venv/bin/python -m src.scraper >> /home/usuario/arca_scraper/logs/cron.log 2>&1

# Todos los lunes a las 7:30 AM
30 7 * * 1 /home/usuario/arca_scraper/venv/bin/python -m src.scraper >> /home/usuario/arca_scraper/logs/cron.log 2>&1

# El primer día de cada mes a las 6:00 AM
0 6 1 * * /home/usuario/arca_scraper/venv/bin/python -m src.scraper >> /home/usuario/arca_scraper/logs/cron.log 2>&1
```

> **Importante:** reemplazar `/home/usuario/arca_scraper` con la ruta absoluta real del proyecto.

### Consideraciones para cron

Cron ejecuta los comandos con un entorno mínimo (sin variables de sesión). Para evitar problemas:

**1. Usar siempre rutas absolutas** — tanto para Python como para el módulo:

```cron
0 8 * * * cd /home/usuario/arca_scraper && /home/usuario/arca_scraper/venv/bin/python -m src.scraper >> /home/usuario/arca_scraper/logs/cron.log 2>&1
```

**2. El archivo `.env` debe existir** en la raíz del proyecto con `BROWSER_HEADLESS=true`.

**3. Los directorios `data/` y `logs/` deben existir** antes de la primera ejecución:

```bash
mkdir -p /home/usuario/arca_scraper/data
mkdir -p /home/usuario/arca_scraper/logs
```

**4. Verificar permisos** — el usuario que ejecuta cron debe tener acceso de escritura a `data/` y `logs/`.

### Verificar que el cron está activo

```bash
# Listar tareas programadas del usuario actual
crontab -l

# Ver logs del demonio cron del sistema
grep CRON /var/log/syslog | tail -20
```

### Sintaxis de cron (referencia rápida)

```
┌───── minuto (0-59)
│ ┌───── hora (0-23)
│ │ ┌───── día del mes (1-31)
│ │ │ ┌───── mes (1-12)
│ │ │ │ ┌───── día de la semana (0=domingo, 1=lunes ... 6=sábado)
│ │ │ │ │
* * * * *  comando
```

## Notas de Seguridad

- Las credenciales se almacenan localmente en `.env` y nunca se envían a otro lugar que no sea ARCA
- El archivo `.gitignore` protege tus credenciales de ser subidas a Git
- Se recomienda usar este script solo en máquinas de tu confianza
- No compartas tus archivos `.env` con nadie

## Limitaciones

- Requiere que el sitio de ARCA esté disponible
- Los selectores HTML pueden cambiar si ARCA actualiza su sitio
- La velocidad de descarga depende de tu conexión y del servidor de ARCA

## Licencia

Este proyecto es de uso personal. Úsalo bajo tu propia responsabilidad.
