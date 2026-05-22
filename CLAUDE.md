# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**arca_scraper** is a Python-based web scraper that automates downloading tax receipts (comprobantes recibidos) from the ARCA website (formerly AFIP - Agencia Federal de Ingresos Públicos, Argentina's federal tax agency).

The scraper uses Playwright to:
1. Authenticate with CUIT (tax ID) and password
2. Navigate to "Mis Comprobantes" section
3. Download CSV files of received receipts (comprobantes recibidos)

## Technology Stack

- **Python 3.8+**
- **Playwright**: Browser automation for handling login and navigation
- **python-dotenv**: Secure credential management via .env files
- **pandas**: CSV data processing (installed but not yet actively used)

## Architecture

### Core Modules

- **src/config.py**: Centralized configuration including URLs, credentials loading, directory paths, and Playwright settings
- **src/authenticator.py**: `ARCAAuthenticator` class handles login flow and navigation to Mis Comprobantes
- **src/downloader.py**: `ComprobantesDownloader` class manages CSV file downloads with optional date filters
- **src/scraper.py**: Main entry point that orchestrates authentication, navigation, and download

### Data Flow

1. Load credentials from `.env` file (via `config.py`)
2. Launch Playwright browser (Chromium)
3. `ARCAAuthenticator.login()` performs authentication
4. `ARCAAuthenticator.navigate_to_comprobantes()` goes to receipts section
5. `ComprobantesDownloader.download_comprobantes_recibidos()` triggers and saves CSV download
6. Files saved to `data/` with timestamp, logs to `logs/`

## Development Commands

### Initial Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure credentials
cp .env.example .env
# Edit .env with real CUIT and password
```

### Running the Scraper

```bash
# Basic execution (downloads all receipts)
python -m src.scraper

# Run from project root
cd /home/sebastian/Documentos/Proyectos/varios/arca_scraper
python -m src.scraper
```

### Testing and Debugging

- **Headless mode**: Set `BROWSER_HEADLESS = True` in `src/config.py` for faster execution without UI
- **Visual debugging**: Default is `BROWSER_HEADLESS = False` to watch the browser navigate
- **Error screenshots**: Automatically saved to `logs/` when operations fail
- **Logs**: All execution logs saved to `logs/arca_scraper_YYYYMMDD_HHMMSS.log`

## Important Files and Directories

- **.env**: Contains ARCA credentials (NEVER commit this file - protected by .gitignore)
- **data/**: Downloaded CSV files stored here with timestamp naming
- **logs/**: Execution logs and error screenshots
- **src/config.py**: Modify timeouts, URLs, or toggle headless mode here

## Configuration Notes

### Credentials Security

- Credentials stored in `.env` file (git-ignored)
- Format: `ARCA_CUIT=20123456789` and `ARCA_PASSWORD=password`
- Loaded via python-dotenv at runtime
- Never hardcode credentials in source files

### URLs (as of implementation)

- Login: `https://auth.afip.gob.ar/contribuyente_/login.xhtml`
- Mis Comprobantes: `https://fes.afip.gob.ar/mcmp/jsp/setearContribuyente.do?idContribuyente=0`
- Comprobantes Recibidos: `https://fes.afip.gob.ar/mcmp/jsp/comprobantesRecibidos.do`

### HTML Selectors

The scraper uses CSS selectors to locate page elements. If ARCA updates their website structure, selectors may need adjustment in:
- `src/authenticator.py`: Login form fields and buttons
- `src/downloader.py`: Date filters and download buttons

Check error screenshots in `logs/` to debug selector issues.

## Common Modifications

### Change Date Range for Downloads

Edit `src/scraper.py` in the `main()` function:

```python
# Uncomment and modify:
fecha_desde = "01/01/2024"
fecha_hasta = "31/12/2024"
archivo_descargado = downloader.download_comprobantes_recibidos(fecha_desde, fecha_hasta)
```

### Adjust Timeouts

In `src/config.py`:
```python
BROWSER_TIMEOUT = 30000  # milliseconds
DOWNLOAD_TIMEOUT = 60000  # milliseconds
```

### Add Custom Filters

Use `downloader.download_with_filters()` method with a dictionary of filters (requires mapping to actual ARCA form fields).

## Maintenance Considerations

1. **Website Changes**: ARCA may update their site structure, requiring selector updates
2. **Authentication Flow**: Multi-factor auth or captcha would require architectural changes
3. **Rate Limiting**: Currently no delay between requests - add if needed
4. **Error Handling**: Screenshots saved automatically for debugging failed operations
