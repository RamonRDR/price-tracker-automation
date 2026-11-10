<div align="center">

# Price Tracker Automation 🏷️

**Monitore preços com responsabilidade. Acompanhe cada mudança. Receba alertas com confiança.**

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

> **Status do projeto:** MVP integrado à `main` após revisão do Codex e correções no [PR #1](https://github.com/RamonRDR/price-tracker-automation/pull/1). O CI usado como evidência do badge aprovou **57 testes unitários/HTTP local + 5 testes Chromium = 62 aprovados**. O monitoramento externo agendado continua desativado; o envio opcional por SMTP não é validado pelo CI contra um servidor de e-mail real.

Uma CLI de monitoramento responsável de preços, desenvolvida com Python 3.14, Playwright, adaptadores HTTP e SQLite. Projeto de portfólio voltado às competências de **Python, Backend, Automação e QA Automation**.

> **Uso responsável:** monitore apenas páginas públicas de demonstração ou fontes que autorizem expressamente a automação. O sistema não contorna autenticação, CAPTCHA, limites de requisições nem restrições de acesso. Os exemplos abaixo usam URLs fictícias ou um arquivo HTML local.

## 1. O que o projeto faz

O sistema cadastra uma URL de produto, extrai nome e preço, grava observações com data e hora, compara preços consecutivos e registra alertas quando um limite configurado é alcançado.

**Destaques**

- Dois adaptadores de extração: **JSON-LD via httpx** e **seletores CSS via Playwright Chromium**.
- Histórico de produtos, preços e alertas persistido em **SQLite / SQLAlchemy**.
- Cálculos financeiros com **Decimal**, incluindo variações positivas e negativas.
- Alertas de preço-alvo e queda percentual, com prevenção de eventos repetidos.
- Monitoramento multiproduto, com limites de tentativas, intervalos e frequência.
- CLI Typer com tabelas Rich, histórico, pausa/retomada e exportação CSV.
- Testes e verificações no GitHub Actions, sem scraping comercial nos PRs.
- Workflow manual, condicionado à aprovação e com armazenamento privado durável.

## 2. Tecnologias

| Camada | Tecnologias |
| --- | --- |
| Execução e validação | Python 3.14, Pydantic |
| Extração | httpx, Playwright (Chromium), JSON-LD em HTML |
| Persistência | SQLite, SQLAlchemy 2 |
| Interface e exportação | Typer, Rich, CSV |
| Notificações | SMTP com STARTTLS (opcional) |
| Testes e qualidade | pytest, pytest-playwright, Ruff |
| Empacotamento e CI | hatchling, Python build, GitHub Actions |

**Precisão das versões:** o CI utiliza Python 3.14; o `pyproject.toml` declara Pydantic `>=2.12,<3` e SQLAlchemy `>=2.0.40,<3`. Portanto, seus badges mostram apenas a **versão principal**, sem inventar uma versão exata. As demais dependências também usam intervalos declarados.

## 3. Arquitetura

~~~text
Usuário → CLI Typer → Serviço de monitoramento → Adaptador
                       │                        ├── JSON-LD / httpx
                       │                        └── CSS / Playwright
                       ├── Validação Pydantic
                       ├── SQLAlchemy → SQLite
                       │               ├── products
                       │               ├── price_observations
                       │               └── alert_events
                       └── Alertas → terminal / SMTP opcional
~~~

| Arquivo | Responsabilidade |
| --- | --- |
| `config.py`, `schemas.py` | Configurações e validação de URLs, produtos e preços |
| `extractors.py` | Extração HTTP/JSON-LD e CSS/Playwright |
| `models.py`, `storage.py` | Modelos, consultas SQLite, transações e eventos |
| `money.py` | Conversão e formatação monetária com Decimal |
| `monitor.py` | Tentativas limitadas, comparação e resultados |
| `notifications.py` | Resumo opcional de alertas por SMTP |
| `cli.py`, `exporter.py` | Interface e exportação segura em CSV |
| `github_runner.py` | Monitoramento autorizado com estado em repositório privado |

Cada verificação bem-sucedida grava a observação e os novos alertas na mesma transação. Decisões técnicas em [ADR-0001](docs/adr/0001-controlled-monitoring.md).

## 4. Instalação

**Pré-requisitos:** Python **3.14**, Git e Chromium instalado pelo Playwright para usar o adaptador CSS. O SQLite não exige servidor.

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

O código da aplicação já está na `main` ([PR #1](https://github.com/RamonRDR/price-tracker-automation/pull/1)); não é necessário alternar para a branch de desenvolvimento.

## 5. Demonstração funcional com HTML local

O repositório contém o produto fictício `tests/fixtures/product.html`. Assim é possível demonstrar o fluxo completo JSON-LD → SQLite → CLI sem consultar lojas comerciais.

**Terminal A** (servidor de demonstração):

~~~bash
python -m http.server 8765 --bind 127.0.0.1 --directory tests/fixtures
~~~

**Terminal B** (ambiente Python ativado):

~~~bash
price-tracker add "http://127.0.0.1:8765/product.html" --target 1300 --drop-percent 10
price-tracker check 1
price-tracker products
price-tracker history 1
price-tracker alerts --product-id 1
price-tracker export --output price-history.csv
~~~

O HTML contém um **Demo Widget** fictício a **USD 1.234,56**. A primeira verificação grava o preço e atende ao alvo de USD 1.300. Para separar essa demonstração de outros dados, passe `--db ./demo-prices.db` em todos os comandos. Os testes do CI usam seu próprio servidor local controlado.

## 6. Referência da CLI

| Comando | Finalidade |
| --- | --- |
| `price-tracker add URL` | Cadastrar uma URL HTTP(S), sem consultar no cadastro |
| `price-tracker products` | Listar produtos e configurações |
| `price-tracker check [ID]` | Consultar um produto ou todos os ativos |
| `price-tracker monitor` | Executar uma ou mais rodadas limitadas |
| `price-tracker history ID` | Ver histórico persistido |
| `price-tracker alerts` | Listar eventos de alerta |
| `price-tracker target ID VALOR` | Definir preço-alvo |
| `price-tracker drop-alert ID PERCENTUAL` | Definir limite de queda percentual |
| `price-tracker pause ID` / `resume ID` | Desativar / reativar um produto |
| `price-tracker export --output ARQUIVO` | Exportar histórico em CSV |

Exemplo fictício com seletores CSS:

~~~bash
price-tracker add "https://demo.example.org/item" \
  --adapter css \
  --name-selector "h1.product-name" \
  --price-selector ".current-price" \
  --currency BRL
price-tracker check 2
~~~

`demo.example.org` é apenas uma URL ilustrativa, não uma loja real nem uma fonte garantida. Consulte `price-tracker --help` e `--help` em cada subcomando.

## 7. Configuração e segurança

As configurações são lidas de variáveis de ambiente. Veja [`.env.example`](.env.example). Arquivos `.env` não são carregados automaticamente e não devem ser publicados.

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `PRICE_TRACKER_DB` | `~/.local/share/price-tracker/prices.db` | Arquivo SQLite, ou utilize `--db` |
| `PRICE_TRACKER_TIMEOUT` | `15` | Timeout HTTP / navegador (segundos) |
| `PRICE_TRACKER_RETRIES` | `2` | Novas tentativas, máximo 4 |
| `PRICE_TRACKER_RETRY_DELAY` | `0.5` | Intervalo inicial entre tentativas |
| `PRICE_TRACKER_DELAY` | `1` | Intervalo entre produtos (segundos) |
| `PRICE_TRACKER_MAX_PRODUCTS` | `50` | Máximo de produtos ativos por rodada |
| `PRICE_TRACKER_SMTP_HOST` | Não definido | Servidor SMTP opcional |
| `PRICE_TRACKER_SMTP_PORT` | `587` quando usado | Porta SMTP com STARTTLS |
| `PRICE_TRACKER_SMTP_FROM` / `_TO` | Não definidos | Remetente e destinatário |
| `PRICE_TRACKER_SMTP_USERNAME` / `_PASSWORD` | Não definidos | Credenciais somente por ambiente |

O histórico fica no SQLite local. Nunca envie segredos, bancos com dados privados ou URLs confidenciais em commits, logs ou artifacts públicos.

## 8. Monitoramento e frequência

~~~bash
# Uma rodada de todos os produtos ativos
price-tracker monitor

# Três rodadas com intervalo de 60 minutos
price-tracker monitor --every-minutes 60 --runs 3

# Uma rodada com possível envio de novos alertas por SMTP
price-tracker check --notify
~~~

A execução não é um loop infinito: há uma rodada por padrão, com limite de 100 rodadas. Erros individuais são informados e não impedem a verificação dos demais produtos. Respeite a política de automação de cada fonte.

## 9. Histórico, comparações e alertas

Cada consulta bem-sucedida gera uma observação com data e hora. `history` mostra registros recentes e `export` grava as colunas `product_id`, `name`, `price`, `currency` e `checked_at` em CSV. Os nomes são protegidos contra interpretação acidental como fórmulas.

- **Preço-alvo:** alerta na primeira observação abaixo/igual ao alvo ou em uma nova passagem de cima para baixo. Consultas repetidas abaixo do limite não criam alertas iguais.
- **Queda percentual:** compara o preço atual à **observação bem-sucedida imediatamente anterior**. Quedas sucessivas que atingem o limite podem produzir eventos distintos.
- **Aumento:** aparece como variação positiva, mas não existe um alerta específico de aumento.
- **Troca de moeda:** a comparação é rejeitada para não misturar moedas diferentes.
- **E-mail:** exige `--notify` e SMTP válido. Os eventos são gravados antes do envio e e-mails malsucedidos **não são reenviados automaticamente**.

## 10. Testes e qualidade

**Evidência dos testes:** a [execução #42732629484 do GitHub Actions](https://github.com/RamonRDR/price-tracker-automation/actions/runs/42732629484) registrou **57 aprovados, 5 desmarcados pela seleção** em `pytest -m "not browser"` e **5 aprovados, 57 desmarcados pela seleção** em `pytest -m browser`. Como são conjuntos separados, o total é **62 aprovados, 0 falhas, 0 ignorados**. Os testes não selecionados em um job são executados no outro. Ruff lint/format e build wheel/sdist também passaram.

**Manutenção do badge:** `pytest | 62 passing` é um **registro estático do CI aprovado**, não um contador em tempo real. Quando os testes mudarem, consulte os dois jobs no novo commit e atualize o valor somente após um CI verde. Não há automação fazendo commits de badges na `main`.

~~~bash
python -m pytest -q -m "not browser"
python -m playwright install chromium
python -m pytest -q -m browser
ruff check .
ruff format --check .
python -m build
~~~

Mocks e servidor HTTP local garantem testes determinísticos para URLs inválidas, preços, formatação monetária, layouts alterados, indisponibilidade, falhas HTTP, timeouts, SQLite, quedas, alvos, deduplicação, CSV e CLI. O CI não consulta lojas externas.

## 11. GitHub Actions

- **`.github/workflows/ci.yml`:** Ruff lint/format, testes Python 3.14 e HTTP local, Playwright Chromium local e build wheel/sdist.
- **`.github/workflows/manual-monitor.yml`:** execução somente manual, condicionada a uma variável e checkbox de aprovação. **Não há cron ativo.**

Como os runners são temporários, após **aprovação separada do proprietário** o monitoramento remoto requer um **repositório privado separado**, com branch `monitor-state` e token de escopo restrito com Contents read/write somente nele. Configurar as variáveis `TRACKER_MONITOR_APPROVED`, `TRACKER_STATE_REPO`, `TRACKER_STATE_BRANCH` e `TRACKER_ALLOWED_HOSTS`; armazenar `TRACKER_STATE_TOKEN` e `TRACKER_PRODUCTS_JSON` (lista JSON de fontes HTTPS autorizadas) como secrets. SMTP é opcional.

O runner sincroniza a lista atual de produtos autorizados antes da consulta e desativa fontes antigas que não estejam mais aprovadas. O Playwright bloqueia redirecionamentos e recursos externos não autorizados **antes da requisição**; por segurança, nenhum redirecionamento é seguido, mesmo que o destino esteja aprovado. O workflow instala o Chromium e suas dependências.

O SQLite durável é baixado pela **API Git Blob**, pois os dados inline da API Contents podem faltar acima de 1 MB. Tamanho e integridade são validados, com limite de 32 MiB e rejeição de arquivos inconsistentes, sem sobrescrever o histórico. O banco é salvo no repositório privado **antes** do envio SMTP, prevenindo alertas repetidos quando o upload falha. E-mails que falham não são reenviados automaticamente.

O runner rejeita repositórios públicos de estado e hosts não autorizados, executa uma única rodada e armazena o SQLite no repositório privado, nunca na `main` pública ou em artifacts públicos. Este projeto **não ativa monitoramento externo nem agendamento recorrente**.

## 12. Limitações conhecidas

- Os adaptadores exigem JSON-LD compatível ou seletores CSS estáveis em fontes autorizadas. Redirecionamentos do navegador são bloqueados, inclusive para destinos autorizados.
- Valores monetários ambíguos podem necessitar de normalização por adaptador.
- SQLite atende monitoramento pequeno/serial, não scraping distribuído em alta escala.
- A queda percentual compara observações consecutivas, não o maior preço histórico.
- Alterar o alvo quando o produto já está abaixo dele não gera novo alerta imediato.
- SMTP não oferece entrega garantida nem fila transacional de e-mails.
- Monitoramento no Actions exige configuração de um repositório privado e aprovação.
- Não há contorno de CAPTCHA, autenticação, técnicas furtivas ou bloqueios.

## 13. Estrutura do repositório

~~~text
price-tracker-automation/
├── .github/workflows/        # CI e monitoramento manual condicionado
├── docs/adr/                 # Decisão de arquitetura e permissões
├── examples/                 # Configuração fictícia de produtos
├── src/price_tracker/        # CLI, adaptadores, banco, alertas, runner
├── tests/                    # Testes unitários, HTTP local e Chromium
├── .env.example              # Exemplos de variáveis de ambiente
├── pyproject.toml            # Dependências e empacotamento Python
├── README.md                 # Guia principal em inglês
├── README.pt-BR.md           # Guia em português brasileiro
├── README.es.md              # Guia em espanhol
└── LICENSE                   # MIT
~~~

## 14. Contribuições

Para propor alterações, trabalhe em uma branch de desenvolvimento e abra um pull request. Execute os testes e as verificações Ruff descritas na [seção 10](#10-testes-e-qualidade) antes de enviar. Use apenas fixtures fictícias ou locais, não publique credenciais nem históricos privados e não ative monitoramento externo sem autorização explícita da fonte.

## 15. Licença

Distribuído sob a [Licença MIT](LICENSE). Os exemplos são fictícios, exceto os arquivos HTML locais incluídos para testes.
