# Guía de despliegue en producción — Ubuntu 22.04 con Systemd Timer

## Índice
1. [Requisitos previos en el servidor](#1-requisitos-previos-en-el-servidor)
2. [Crear usuario dedicado](#2-crear-usuario-dedicado)
3. [Preparar el directorio del proyecto](#3-preparar-el-directorio-del-proyecto)
4. [Clonar e instalar el proyecto](#4-clonar-e-instalar-el-proyecto)
5. [Instalar Playwright y Chromium](#5-instalar-playwright-y-chromium)
6. [Configurar credenciales](#6-configurar-credenciales)
7. [Verificar ejecución manual](#7-verificar-ejecución-manual)
8. [Crear el servicio systemd](#8-crear-el-servicio-systemd)
9. [Crear el timer systemd](#9-crear-el-timer-systemd)
10. [Activar y verificar](#10-activar-y-verificar)
11. [Monitoreo y logs](#11-monitoreo-y-logs)
12. [Mantenimiento](#12-mantenimiento)

---

## 1. Requisitos previos en el servidor

Actualizar el sistema e instalar dependencias base:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git
```

Verificar versión de Python (debe ser 3.8 o superior):

```bash
python3 --version
```

---

## 2. Crear usuario dedicado

Crear un usuario sin shell de login para aislar la ejecución del scraper:

```bash
sudo useradd -r -m -d /opt/arca_scraper -s /usr/sbin/nologin arca
```

> `-r`: usuario del sistema | `-m`: crea el home | `-d /opt/arca_scraper`: el home será el directorio del proyecto | `-s /usr/sbin/nologin`: sin acceso interactivo

---

## 3. Preparar el directorio del proyecto

El home del usuario `arca` ya es `/opt/arca_scraper`, pero verificar permisos y crear subdirectorios necesarios:

```bash
sudo mkdir -p /opt/arca_scraper/data
sudo mkdir -p /opt/arca_scraper/logs
sudo chown -R arca:arca /opt/arca_scraper
```

---

## 4. Clonar e instalar el proyecto

Ejecutar como usuario `arca` mediante `sudo -u arca`:

```bash
# Clonar el repositorio en el directorio del proyecto
sudo -u arca git clone <URL_DEL_REPOSITORIO> /opt/arca_scraper

# Crear el entorno virtual
sudo -u arca python3 -m venv /opt/arca_scraper/venv

# Instalar dependencias Python
sudo -u arca /opt/arca_scraper/venv/bin/pip install --upgrade pip
sudo -u arca /opt/arca_scraper/venv/bin/pip install -r /opt/arca_scraper/requirements.txt
```

> Si no usás Git, copiá la carpeta del proyecto con `scp` o `rsync` y luego ajustá los permisos con `sudo chown -R arca:arca /opt/arca_scraper`.

---

## 5. Instalar Playwright y Chromium

Instalar el navegador Chromium dentro del entorno del usuario `arca`:

```bash
# Instalar Chromium para Playwright (como usuario arca)
sudo -u arca /opt/arca_scraper/venv/bin/playwright install chromium

# Instalar dependencias del sistema para Chromium (como root)
sudo /opt/arca_scraper/venv/bin/playwright install-deps chromium
```

> En Ubuntu 22.04, `playwright install-deps` funciona directamente. Si en el futuro migrás a Ubuntu 24.04, revisá la sección de instalación manual en el README.

Verificar que Chromium funciona en modo headless:

```bash
sudo -u arca /opt/arca_scraper/venv/bin/python -c \
  "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); print('Chromium OK'); b.close(); p.stop()"
```

Debe imprimir `Chromium OK`.

---

## 6. Configurar credenciales

Crear el archivo `.env` a partir del ejemplo:

```bash
sudo -u arca cp /opt/arca_scraper/.env.example /opt/arca_scraper/.env
sudo -u arca nano /opt/arca_scraper/.env
```

Contenido del archivo `.env`:

```env
ARCA_CUIT=20123456789
ARCA_PASSWORD=tu_password_real
ARCA_REPRESENTADO_CUIT=20123456789
ARCA_REPRESENTADO_NOMBRE=Nombre del Representado
BROWSER_HEADLESS=true
```

> `BROWSER_HEADLESS=true` es **obligatorio** en servidor sin entorno gráfico.

Proteger el archivo de credenciales:

```bash
sudo chmod 600 /opt/arca_scraper/.env
sudo chown arca:arca /opt/arca_scraper/.env
```

---

## 7. Verificar ejecución manual

Antes de configurar el timer, confirmar que el scraper funciona correctamente de forma manual:

```bash
sudo -u arca bash -c "cd /opt/arca_scraper && /opt/arca_scraper/venv/bin/python -m src.scraper"
```

Verificar que se crearon archivos en `data/` y `logs/`:

```bash
ls -la /opt/arca_scraper/data/
ls -la /opt/arca_scraper/logs/
```

---

## 8. Crear el servicio systemd

El **service** define *qué* ejecutar. Crear el archivo:

```bash
sudo nano /etc/systemd/system/arca-scraper.service
```

Contenido:

```ini
[Unit]
Description=ARCA Scraper - Descarga automática de comprobantes
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=arca
Group=arca
WorkingDirectory=/opt/arca_scraper
ExecStart=/opt/arca_scraper/venv/bin/python -m src.scraper
StandardOutput=journal
StandardError=journal
SyslogIdentifier=arca-scraper

# Seguridad adicional
NoNewPrivileges=true
PrivateTmp=true
```

> `Type=oneshot` indica que el servicio termina cuando el proceso finaliza — correcto para scripts que se ejecutan y terminan.

---

## 9. Crear el timer systemd

El **timer** define *cuándo* ejecutar el servicio. Crear el archivo:

```bash
sudo nano /etc/systemd/system/arca-scraper.timer
```

Contenido (ejemplo: todos los días hábiles a las 8:00 AM):

```ini
[Unit]
Description=Timer para ARCA Scraper - Ejecución diaria
Requires=arca-scraper.service

[Timer]
OnCalendar=Mon..Fri 08:00:00
AccuracySec=1min
Persistent=true

[Install]
WantedBy=timers.target
```

**Opciones de frecuencia** — ajustar `OnCalendar` según necesidad:

```ini
# Todos los días a las 8:00 AM
OnCalendar=*-*-* 08:00:00

# Lunes a viernes a las 8:00 AM
OnCalendar=Mon..Fri 08:00:00

# Todos los lunes a las 7:30 AM
OnCalendar=Mon 07:30:00

# El primer día de cada mes a las 6:00 AM
OnCalendar=*-*-1 06:00:00
```

> `Persistent=true`: si el servidor estuvo apagado en el horario programado, ejecuta la tarea al encender.

---

## 10. Activar y verificar

Recargar systemd para detectar los nuevos archivos:

```bash
sudo systemctl daemon-reload
```

Habilitar e iniciar el timer:

```bash
sudo systemctl enable arca-scraper.timer
sudo systemctl start arca-scraper.timer
```

Verificar que el timer está activo:

```bash
sudo systemctl status arca-scraper.timer
```

Ver todos los timers activos y cuándo se ejecutarán:

```bash
systemctl list-timers --all | grep arca
```

Probar el servicio manualmente (sin esperar al timer):

```bash
sudo systemctl start arca-scraper.service
sudo systemctl status arca-scraper.service
```

---

## 11. Monitoreo y logs

Ver logs en tiempo real del scraper:

```bash
sudo journalctl -u arca-scraper.service -f
```

Ver los últimos logs de la última ejecución:

```bash
sudo journalctl -u arca-scraper.service -n 100
```

Ver logs del timer (ejecuciones programadas):

```bash
sudo journalctl -u arca-scraper.timer
```

Ver logs de todas las ejecuciones desde el inicio:

```bash
sudo journalctl -u arca-scraper.service --since "7 days ago"
```

Ver archivos de log propios del scraper:

```bash
ls -la /opt/arca_scraper/logs/
tail -f /opt/arca_scraper/logs/arca_scraper_*.log
```

---

## 12. Mantenimiento

### Actualizar el código

```bash
sudo -u arca bash -c "cd /opt/arca_scraper && git pull"
sudo systemctl restart arca-scraper.timer
```

### Cambiar la frecuencia del timer

```bash
sudo nano /etc/systemd/system/arca-scraper.timer
sudo systemctl daemon-reload
sudo systemctl restart arca-scraper.timer
```

### Desactivar temporalmente

```bash
sudo systemctl stop arca-scraper.timer
sudo systemctl disable arca-scraper.timer
```

### Verificar permisos de directorios

```bash
ls -la /opt/arca_scraper/data/
ls -la /opt/arca_scraper/logs/
# Deben ser propiedad del usuario arca
```

---

> **Resumen de archivos creados en el servidor:**
> - `/opt/arca_scraper/` — directorio del proyecto
> - `/opt/arca_scraper/.env` — credenciales (permisos 600)
> - `/etc/systemd/system/arca-scraper.service` — definición del servicio
> - `/etc/systemd/system/arca-scraper.timer` — programación de ejecución
