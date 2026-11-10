<div align="center">

# Price Tracker Automation 🏷️

**Supervisa precios responsablemente. Sigue cada cambio. Recibe alertas con confianza.**

[🇺🇸 English](README.md) · [🇧🇷 Português](README.pt-BR.md) · [🇪🇸 Español](README.es.md)

[![CI](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml)
[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue)](https://www.python.org/)
[![MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063)](https://docs.pydantic.dev/latest/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-2EAD33)](https://playwright.dev/python/)
[![httpx](https://img.shields.io/badge/httpx-HTTP-4C78A8)](https://www.python-httpx.org/)
[![SQLite](https://img.shields.io/badge/SQLite-history-003B57)](https://www.sqlite.org/)
[![SQLAlchemy 2](https://img.shields.io/badge/SQLAlchemy-2-D71F00)](https://www.sqlalchemy.org/)
[![Typer](https://img.shields.io/badge/Typer-CLI-007C6C)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Rich-terminal-6C63FF)](https://rich.readthedocs.io/en/stable/)
[![hatchling](https://img.shields.io/badge/hatchling-packaging-663399)](https://hatch.pypa.io/latest/)

[![pytest](https://img.shields.io/badge/pytest-62%20passing-0A9EDC)](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484)
[![Chromium tests](https://img.shields.io/badge/Chromium-5%20passing-4A90E2)](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484)
[![Ruff](https://img.shields.io/badge/Ruff-lint%20%26%20format-D7FF64)](https://docs.astral.sh/ruff/)
[![Build](https://img.shields.io/badge/Build-wheel%20%2B%20sdist-passing-555555)](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484)

</div>

> **Estado del proyecto:** MVP integrado en `main` tras la revisión de Codex y la resolución de problemas en el [PR #1](https://github.com/RamonRDR/price-tracker-automation/pull/1). El CI que respalda el badge aprobó **57 pruebas unitarias/HTTP local + 5 pruebas Chromium = 62 aprobadas**. El monitoreo externo programado sigue desactivado; el envío SMTP opcional no se valida con un servidor de correo real en CI.

Una CLI para el seguimiento responsable de precios, creada con Python 3.14, Playwright, adaptadores HTTP y SQLite. Proyecto de portafolio para puestos de **Python, Backend, Automatización y QA Automation**.

> **Uso responsable:** consulta únicamente páginas públicas de demostración o fuentes que permitan expresamente la automatización. No evita autenticación, CAPTCHA, límites de solicitudes ni restricciones de acceso. Los ejemplos utilizan URL ficticias o una página HTML local.

## 1. ¿Qué hace?

El sistema registra una URL de producto, extrae el nombre y el precio actual, guarda observaciones con fecha y hora, compara precios consecutivos y registra alertas cuando se alcanza un umbral.

**Funciones principales**

- Dos adaptadores configurables: **JSON-LD mediante httpx** y **selectores CSS mediante Playwright Chromium**.
- Historial de productos, precios y alertas en **SQLite / SQLAlchemy**.
- Cálculos monetarios con **Decimal**, incluyendo subidas y bajadas.
- Alertas de precio objetivo y caída porcentual, evitando eventos repetidos.
- Seguimiento de varios productos con reintentos e intervalos limitados.
- CLI Typer con tablas Rich, historial, pausa/reanudación y CSV.
- Pruebas y verificaciones en GitHub Actions, sin scraping comercial en los PR.
- Workflow manual sujeto a aprobación y almacenamiento privado persistente.

## 2. Tecnologías

| Área | Tecnologías |
| --- | --- |
| Ejecución y validación | Python 3.14, Pydantic |
| Extracción | httpx, Playwright (Chromium), JSON-LD en HTML |
| Persistencia | SQLite, SQLAlchemy 2 |
| Interfaz y exportación | Typer, Rich, CSV |
| Notificaciones | SMTP con STARTTLS (opcional) |
| Pruebas y calidad | pytest, pytest-playwright, Ruff |
| Paquetes y CI | hatchling, Python build, GitHub Actions |

**Versiones verificadas:** CI utiliza Python 3.14; `pyproject.toml` declara Pydantic `>=2.12,<3` y SQLAlchemy `>=2.0.40,<3`. Por tanto, los badges indican su **versión principal** y no una instalación exacta no confirmada. Las demás dependencias también están definidas mediante intervalos.

## 3. Arquitectura

~~~text
Usuario → CLI Typer → Servicio de monitoreo → Adaptador
                       │                      ├── JSON-LD / httpx
                       │                      └── CSS / Playwright
                       ├── Validación Pydantic
                       ├── SQLAlchemy → SQLite
                       │               ├── products
                       │               ├── price_observations
                       │               └── alert_events
                       └── Alertas → consola / SMTP opcional
~~~

| Archivo | Responsabilidad |
| --- | --- |
| `config.py`, `schemas.py` | Variables de configuración, URL, productos y precios |
| `extractors.py` | Extracción HTTP/JSON-LD y CSS/Playwright |
| `models.py`, `storage.py` | Modelos, consultas SQLite, transacciones y alertas |
| `money.py` | Conversión y formato monetario con Decimal |
| `monitor.py` | Reintentos limitados, comparaciones y resultados |
| `notifications.py` | Resumen opcional de alertas por SMTP |
| `cli.py`, `exporter.py` | Comandos y exportación segura a CSV |
| `github_runner.py` | Ejecución autorizada con estado en repositorio privado |

Cada comprobación válida almacena la observación y los nuevos eventos en una misma transacción. Véase [ADR-0001](docs/adr/0001-controlled-monitoring.md).

## 4. Instalación

**Requisitos:** Python **3.14**, Git y Chromium instalado con Playwright para el adaptador CSS. SQLite no requiere servidor.

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

El código de la aplicación ya está en `main` ([PR #1](https://github.com/RamonRDR/price-tracker-automation/pull/1)); no hace falta cambiar a una rama de desarrollo.

## 5. Demostración funcional con HTML local

El repositorio incluye el archivo ficticio `tests/fixtures/product.html`. Permite probar el recorrido JSON-LD → SQLite → CLI sin acceder a tiendas reales.

**Terminal A** (servidor local):

~~~bash
python -m http.server 8765 --bind 127.0.0.1 --directory tests/fixtures
~~~

**Terminal B** (entorno Python activo):

~~~bash
price-tracker add "http://127.0.0.1:8765/product.html" --target 1300 --drop-percent 10
price-tracker check 1
price-tracker products
price-tracker history 1
price-tracker alerts --product-id 1
price-tracker export --output price-history.csv
~~~

El HTML contiene un **Demo Widget** ficticio de **USD 1.234,56**. La primera comprobación almacena el precio y alcanza el objetivo de USD 1.300. Para aislar los datos, utiliza `--db ./demo-prices.db` en todos los comandos. Las pruebas de CI utilizan su propio servidor local controlado.

## 6. Referencia de la CLI

| Comando | Objetivo |
| --- | --- |
| `price-tracker add URL` | Registrar una URL HTTP(S) sin consultar al registrarla |
| `price-tracker products` | Listar productos y ajustes |
| `price-tracker check [ID]` | Revisar un producto o todos los activos |
| `price-tracker monitor` | Ejecutar un número limitado de rondas |
| `price-tracker history ID` | Mostrar el historial guardado |
| `price-tracker alerts` | Consultar eventos de alerta |
| `price-tracker target ID IMPORTE` | Configurar precio objetivo |
| `price-tracker drop-alert ID PORCENTAJE` | Configurar caída porcentual |
| `price-tracker pause ID` / `resume ID` | Desactivar / reactivar un producto |
| `price-tracker export --output ARCHIVO` | Exportar historial a CSV |

Ejemplo ficticio con CSS:

~~~bash
price-tracker add "https://demo.example.org/item" \
  --adapter css \
  --name-selector "h1.product-name" \
  --price-selector ".current-price" \
  --currency EUR
price-tracker check 2
~~~

`demo.example.org` es una URL ilustrativa, no una tienda ni una fuente funcional garantizada. Consulta `price-tracker --help` y `--help` en cada subcomando.

## 7. Configuración y seguridad

La aplicación lee variables de entorno. Véase [`.env.example`](.env.example). Los archivos `.env` no se cargan automáticamente y no deben publicarse.

| Variable | Valor inicial | Uso |
| --- | --- | --- |
| `PRICE_TRACKER_DB` | `~/.local/share/price-tracker/prices.db` | Archivo SQLite, o usar `--db` |
| `PRICE_TRACKER_TIMEOUT` | `15` | Timeout de HTTP / navegador (segundos) |
| `PRICE_TRACKER_RETRIES` | `2` | Reintentos adicionales, máximo 4 |
| `PRICE_TRACKER_RETRY_DELAY` | `0.5` | Espera inicial entre intentos |
| `PRICE_TRACKER_DELAY` | `1` | Espera entre productos (segundos) |
| `PRICE_TRACKER_MAX_PRODUCTS` | `50` | Máximo de productos por ronda |
| `PRICE_TRACKER_SMTP_HOST` | No definido | Servidor SMTP opcional |
| `PRICE_TRACKER_SMTP_PORT` | `587` si se usa | Puerto SMTP con STARTTLS |
| `PRICE_TRACKER_SMTP_FROM` / `_TO` | No definidos | Remitente y destinatario |
| `PRICE_TRACKER_SMTP_USERNAME` / `_PASSWORD` | No definidos | Credenciales solo por entorno |

El historial permanece en SQLite local. No publiques secretos, bases de datos privadas ni URL confidenciales en commits, logs o artifacts públicos.

## 8. Monitoreo y frecuencia

~~~bash
# Una ronda con todos los productos activos
price-tracker monitor

# Tres rondas separadas por 60 minutos
price-tracker monitor --every-minutes 60 --runs 3

# Una ronda con notificaciones SMTP opcionales
price-tracker check --notify
~~~

No hay un bucle infinito: una ronda por defecto y un máximo de 100. Los errores individuales se comunican y no detienen las verificaciones de los demás productos. Respeta las políticas de automatización de cada fuente.

## 9. Historial, comparaciones y alertas

Cada comprobación correcta produce una observación con fecha y hora. `history` muestra los registros recientes; `export` escribe un CSV con `product_id`, `name`, `price`, `currency` y `checked_at`. Los nombres se protegen para reducir el riesgo de fórmulas de hoja de cálculo.

- **Precio objetivo:** se activa con la primera observación igual o inferior al límite, o al volver a cruzar desde arriba. Repetir precios bajos no crea alertas repetidas.
- **Caída porcentual:** compara con la **observación correcta inmediatamente anterior**. Caídas consecutivas suficientemente grandes pueden crear eventos diferentes.
- **Subida de precio:** aparece como cambio positivo, pero no tiene una alerta independiente.
- **Cambio de moneda:** la comparación se rechaza para evitar resultados incorrectos.
- **Correo:** requiere `--notify` y SMTP configurado. Los eventos se guardan antes de enviar y los correos fallidos **no se reenvían automáticamente**.

## 10. Pruebas y calidad

**Resultados verificados:** la [ejecución #42732629484 de GitHub Actions](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484) registró **57 aprobadas, 5 excluidas por selección** con `pytest -m "not browser"` y **5 aprobadas, 57 excluidas por selección** con `pytest -m browser`. Son dos grupos separados: **62 aprobadas, 0 fallidas, 0 omitidas**. Las pruebas excluidas de un job se ejecutan en el otro. Ruff lint/format y la construcción wheel/sdist también pasaron.

**Mantenimiento del badge:** `pytest | 62 passing` es una **instantánea estática del CI aprobado**, no un contador en tiempo real. Si cambian las pruebas, verifica ambos jobs en el nuevo commit y actualiza la cifra solamente después de un CI correcto. Ningún workflow realiza commits automáticos de badges en `main`.

~~~bash
python -m pytest -q -m "not browser"
python -m playwright install chromium
python -m pytest -q -m browser
ruff check .
ruff format --check .
python -m build
~~~

Las pruebas utilizan mocks y un servidor HTTP local: validación de URL, precios, formatos monetarios, cambios de HTML, productos no disponibles, fallos HTTP, timeouts, SQLite, objetivos, caídas, duplicados, CSV y CLI. CI no depende de sitios comerciales.

## 11. GitHub Actions

- **`.github/workflows/ci.yml`:** Ruff lint/format, pruebas Python 3.14 y HTTP local, Playwright Chromium con HTML local y construcción wheel/sdist.
- **`.github/workflows/manual-monitor.yml`:** solo ejecución manual, con variable de aprobación y casilla explícita. **No existe cron activo.**

Debido al almacenamiento temporal de los runners, tras una **autorización separada del propietario** el monitoreo remoto necesita un **repositorio privado independiente** con rama `monitor-state` y un token fino con acceso Contents read/write solamente allí. Configura `TRACKER_MONITOR_APPROVED`, `TRACKER_STATE_REPO`, `TRACKER_STATE_BRANCH` y `TRACKER_ALLOWED_HOSTS` como variables; `TRACKER_STATE_TOKEN` y `TRACKER_PRODUCTS_JSON` (lista JSON de fuentes HTTPS autorizadas) como secretos. SMTP es opcional.

El runner sincroniza la lista vigente de productos autorizados antes de consultar y desactiva las fuentes antiguas que hayan perdido autorización. Playwright bloquea redirecciones y recursos externos no autorizados **antes de enviar solicitudes**; por seguridad, no sigue ninguna redirección, incluso cuando el destino está aprobado. El workflow instala Chromium y sus dependencias.

El estado SQLite se recupera mediante la **API Git Blob**, porque los datos inline de Contents pueden faltar por encima de 1 MB. Se comprueban el tamaño y la integridad, con límite de 32 MiB, y se rechazan archivos incorrectos sin sobrescribir el historial. Los cambios se guardan en el repositorio privado **antes** de enviar correos SMTP, evitando notificaciones duplicadas cuando falla la subida. Los correos fallidos no se reenvían automáticamente.

El runner rechaza repositorios de estado públicos y hosts no autorizados, ejecuta una sola ronda y guarda SQLite en el repositorio privado, nunca en la `main` pública ni en artifacts públicos. El proyecto **no activa monitoreo externo ni programación recurrente**.

## 12. Limitaciones conocidas

- Los adaptadores necesitan JSON-LD compatible o selectores CSS estables en fuentes autorizadas. Las redirecciones del navegador se bloquean, incluso hacia destinos aprobados.
- Los formatos monetarios ambiguos pueden requerir normalización específica.
- SQLite es adecuado para cargas pequeñas/seriales, no scraping distribuido de alta frecuencia.
- La caída porcentual usa observaciones consecutivas, no el máximo histórico.
- Cambiar el objetivo cuando el precio ya está por debajo no crea otra alerta inmediata.
- SMTP no garantiza entrega ni ofrece una cola transaccional de correos.
- El monitoreo en Actions necesita repositorio privado configurado y autorización expresa.
- No se incluyen técnicas para eludir CAPTCHA, autenticación, bloqueos o restricciones.

## 13. Estructura del repositorio

~~~text
price-tracker-automation/
├── .github/workflows/        # CI y monitoreo manual aprobado
├── docs/adr/                 # Decisión de diseño y permisos
├── examples/                 # Configuración ficticia de productos
├── src/price_tracker/        # CLI, adaptadores, SQLite, alertas, runner
├── tests/                    # Pruebas unitarias, HTTP local y Chromium
├── .env.example              # Ejemplos de variables de entorno
├── pyproject.toml            # Dependencias y empaquetado Python
├── README.md                 # Guía principal en inglés
├── README.pt-BR.md           # Guía en portugués brasileño
├── README.es.md              # Guía en español
└── LICENSE                   # MIT
~~~

## 14. Contribuciones

Para proponer cambios, utiliza una rama de trabajo y abre un pull request. Ejecuta las pruebas y las verificaciones Ruff de la [sección 10](#10-pruebas-y-calidad) antes de enviar el PR. Utiliza solo fixtures ficticias o locales, no publiques secretos ni historiales privados y no actives el monitoreo externo sin autorización explícita de la fuente.

## 15. Licencia

Distribuido bajo la [Licencia MIT](LICENSE). Todos los productos de ejemplo son ficticios, salvo los archivos HTML locales incluidos para las pruebas.
