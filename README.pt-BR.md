# Price Tracker Automation

[![CI](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml)

**Idiomas:** [English (principal)](README.md) | Português (Brasil) | [Español](README.es.md)

## 1. Objetivo

CLI Python profissional para monitorar preços de maneira responsável. Demonstra Playwright, integração HTTP, persistência, validação, testes e automação CI. **Somente páginas públicas de demonstração ou fontes que autorizem automação.** Não contorna CAPTCHA, autenticação nem bloqueios.

## 2. Funcionalidades implementadas

Cadastro por URL, adaptadores JSON-LD/httpx e CSS/Playwright, histórico SQLite, aumentos/reduções, preço-alvo, queda percentual, alertas não duplicados, CSV, SMTP opcional, pausa/retomada, execução com frequência e quantidade finitas, testes determinísticos e workflows de CI. Monitoramento externo fica desativado até aprovação.

## 3. Tecnologias

Python 3.14, Playwright, httpx, SQLite, SQLAlchemy, Pydantic, Typer, Rich, pytest, pytest-playwright, Ruff, GitHub Actions e hatchling.

## 4. Arquitetura

`config.py` e `schemas.py` validam a configuração; `extractors.py` extrai; `models.py` e `storage.py` persistem; `monitor.py` compara e gera eventos; `notifications.py` envia e-mail; `cli.py` e `exporter.py` exibem/exportam; `github_runner.py` sincroniza um SQLite privado em Actions. Registros e alertas são transacionados em conjunto. Veja [ADR-0001](docs/adr/0001-controlled-monitoring.md).

## 5. Instalação

Requer Python **3.14**.

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

## 6. Exemplos de comandos

URLs **fictícias**:

~~~bash
price-tracker add "https://demo.example.org/produto" --target 80 --drop-percent 10
price-tracker products
price-tracker check 1
price-tracker history 1
price-tracker alerts --product-id 1
price-tracker target 1 75
price-tracker drop-alert 1 15
price-tracker export --output historico.csv
price-tracker pause 1
price-tracker resume 1
price-tracker add "https://demo.example.org/item" --adapter css \
  --name-selector "h1.nome" --price-selector ".preco" --currency BRL
~~~

Adicionar URL não faz requisições externas.

## 7. Configuração

Exemplo no [`.env.example`](.env.example). Banco: `PRICE_TRACKER_DB` ou `--db`. Limites: `PRICE_TRACKER_TIMEOUT=15`, `PRICE_TRACKER_RETRIES=2`, `PRICE_TRACKER_RETRY_DELAY=0.5`, `PRICE_TRACKER_DELAY=1`, `PRICE_TRACKER_MAX_PRODUCTS=50`. SMTP opcional usa `PRICE_TRACKER_SMTP_HOST`, `_FROM`, `_TO`, `_USERNAME` e `_PASSWORD`. O aplicativo não carrega `.env` automaticamente. Nunca publique segredos.

## 8. Monitoramento

~~~bash
price-tracker monitor
price-tracker monitor --every-minutes 60 --runs 3
price-tracker check --notify
~~~

Todas as execuções têm limite. As consultas precisam respeitar as permissões de cada fonte.

## 9. Histórico e alertas

`history` consulta valores e horários UTC; `alerts` mostra eventos; `export` grava CSV. O alvo dispara na primeira consulta abaixo ou igual ao limite e novamente após retornar acima e cruzar de novo. A queda percentual compara observações consecutivas. Os preços são Decimal e alertas não são duplicados em preços inalterados. Falhas SMTP são registradas, **sem reenvio automático**.

## 10. Testes

~~~bash
python -m pytest -q -m "not browser"
python -m playwright install chromium
python -m pytest -q -m browser
ruff check .
ruff format --check .
python -m build
~~~

Testes com mocks e servidor HTML local, sem lojas comerciais. Incluem URLs inválidas, valores monetários, layouts alterados, indisponibilidade, timeouts, persistência, alertas, CSV e CLI.

## 11. GitHub Actions

`ci.yml` usa runners padrão para Ruff, Python 3.14, Playwright local e build. Não há scraping comercial nos PRs. `manual-monitor.yml` está restrito a execução manual com checkbox e variável `TRACKER_MONITOR_APPROVED=true`, não havendo cron ativo. Depois da autorização: criar **repositório privado separado** com branch `monitor-state`; usar token de escopo limitado (Contents read/write); configurar variáveis `TRACKER_STATE_REPO`, `TRACKER_STATE_BRANCH`, `TRACKER_ALLOWED_HOSTS` e segredos `TRACKER_STATE_TOKEN` e `TRACKER_PRODUCTS_JSON` (URLs HTTPS autorizadas). Exemplo fictício: `[{"url":"https://demo.example.org/produto","adapter":"jsonld"}]`. SQLite é salvo no repositório privado, não na main nem em artifacts públicos. Ativação de cron requer aprovação separada.

## 12. Limitações

Adaptadores exigem JSON-LD compatível ou CSS estável; valores ambíguos precisam de normalização; SQLite atende baixa concorrência; queda porcentual compara duas consultas consecutivas; alteração de alvo durante queda ativa não gera alerta imediato; SMTP não tem reenvio; cron não está ativo; não há técnicas de contorno de bloqueios.

## 13. Licença

[MIT](LICENSE). Produtos de exemplo são fictícios. Uso permitido somente em fontes autorizadas.
