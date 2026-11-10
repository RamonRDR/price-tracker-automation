# Price Tracker Automation

[![CI](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/RamonRDR/price-tracker-automation/actions/workflows/ci.yml)
![Python 3.14](https://img.shields.io/badge/Python-3.14-blue)
[![Licença MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Idioma:** [English (principal)](README.md) | **Português (Brasil)** | [Español](README.es.md)

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

**Enquanto o PR #1 não for integrado**, execute `git switch feat/price-tracker-complete-mvp` depois do clone, pois a implementação ainda não está na `main`.

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

## 13. Licença

Distribuído sob a [Licença MIT](LICENSE). Os exemplos são fictícios, exceto os arquivos HTML locais incluídos para testes.
