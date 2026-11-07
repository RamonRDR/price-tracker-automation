# Price Tracker Automation

[![CI](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml)

**Idiomas:** [English (principal)](README.md) | [Português](README.pt-BR.md) | Español

## 1. Objetivo

CLI Python profesional para supervisar precios de manera responsable, demostrando Playwright, HTTP, persistencia, validación, pruebas y CI. Solo usa **páginas públicas de demostración o fuentes que autoricen automatización**. No evade CAPTCHA, autenticación ni bloqueos.

## 2. Funcionalidades

Registro por URL, adaptadores JSON-LD/httpx y CSS/Playwright, historial SQLite, subidas y bajadas, precio objetivo, caída porcentual, alertas sin duplicación, CSV, SMTP opcional, pausa/reactivación, frecuencia y número de pasadas limitados, tests deterministas y GitHub Actions. Monitorización externa inactiva hasta aprobación.

## 3. Tecnologías

Python 3.14, Playwright, httpx, SQLite, SQLAlchemy, Pydantic, Typer, Rich, pytest, pytest-playwright, Ruff, GitHub Actions y hatchling.

## 4. Arquitectura

`config.py` y `schemas.py` validan; `extractors.py` extrae; `models.py` y `storage.py` persisten; `monitor.py` compara y crea eventos; `notifications.py` envía correos; `cli.py` y `exporter.py` presentan/exportan; `github_runner.py` sincroniza SQLite privado en Actions. Una transacción almacena observaciones y alertas. Véase [ADR-0001](docs/adr/0001-controlled-monitoring.md).

## 5. Instalación

Requiere Python **3.14**.

~~~bash
git clone https://github.com/RamonRDR/price-tracker-automation.git
cd price-tracker-automation
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m playwright install chromium
price-tracker --help
~~~

## 6. Ejemplos de comandos

URLs **ficticias**:

~~~bash
price-tracker add "https://demo.example.org/producto" --target 80 --drop-percent 10
price-tracker products
price-tracker check 1
price-tracker history 1
price-tracker alerts --product-id 1
price-tracker target 1 75
price-tracker drop-alert 1 15
price-tracker export --output historial.csv
price-tracker pause 1
price-tracker resume 1
price-tracker add "https://demo.example.org/item" --adapter css \
  --name-selector "h1.product-name" --price-selector ".price" --currency EUR
~~~

Registrar un producto no inicia una petición externa.

## 7. Configuración

Ejemplo [`.env.example`](.env.example). Base de datos: `PRICE_TRACKER_DB` o `--db`. Límites: `PRICE_TRACKER_TIMEOUT=15`, `PRICE_TRACKER_RETRIES=2`, `PRICE_TRACKER_RETRY_DELAY=0.5`, `PRICE_TRACKER_DELAY=1` y `PRICE_TRACKER_MAX_PRODUCTS=50`. SMTP usa `PRICE_TRACKER_SMTP_HOST`, `_FROM`, `_TO`, `_USERNAME` y `_PASSWORD`. No se carga `.env` automáticamente. Nunca publiques credenciales.

## 8. Supervisión

~~~bash
price-tracker monitor
price-tracker monitor --every-minutes 60 --runs 3
price-tracker check --notify
~~~

Las pasadas son finitas y las fuentes deben permitir su consulta automatizada.

## 9. Historial y alertas

`history` consulta precios y timestamps UTC; `alerts` muestra eventos; `export` produce CSV. El precio objetivo alerta al cruzar desde arriba hacia un valor menor o igual. La caída porcentual compara **observaciones consecutivas**. El dinero usa Decimal, los precios repetidos no duplican alertas y el correo SMTP no cuenta con reenvío automático si falla.

## 10. Pruebas

~~~bash
python -m pytest -q -m "not browser"
python -m playwright install chromium
python -m pytest -q -m browser
ruff check .
ruff format --check .
python -m build
~~~

Pruebas con mocks y servidor HTML local sin sitios comerciales; cubren URLs inválidas, precios, fallos HTTP, timeouts, cambios de layout, SQLite, alertas, CSV y CLI.

## 11. GitHub Actions

`ci.yml` valida Ruff, Python 3.14, Playwright sobre HTML local y paquetes. Los PRs no hacen scraping real. `manual-monitor.yml` solo funciona manualmente con aprobación explícita, checkbox y `TRACKER_MONITOR_APPROVED=true`. **No existe cron activo**. Tras autorización, crear un **repositorio privado separado** con rama `monitor-state` y un token de alcance limitado con permiso Contents read/write; definir variables `TRACKER_STATE_REPO`, `TRACKER_STATE_BRANCH` y `TRACKER_ALLOWED_HOSTS`, más secretos `TRACKER_STATE_TOKEN` y `TRACKER_PRODUCTS_JSON`. Ejemplo ficticio: `[{"url":"https://demo.example.org/producto","adapter":"jsonld"}]`. SQLite se guarda en el repositorio privado y nunca en la rama main pública ni en artifacts públicos. Cron requiere autorización adicional.

## 12. Limitaciones

Los adaptadores requieren JSON-LD compatible o CSS estable; formatos monetarios ambiguos pueden necesitar normalización; SQLite está previsto para carga pequeña; las bajadas se calculan entre consultas; cambiar el objetivo durante un episodio de bajo precio no produce alerta inmediata; SMTP no garantiza entrega; cron desactivado; no se permite evasión de bloqueos.

## 13. Licencia

[MIT](LICENSE). Los productos de ejemplo son ficticios; la automatización debe estar autorizada.
