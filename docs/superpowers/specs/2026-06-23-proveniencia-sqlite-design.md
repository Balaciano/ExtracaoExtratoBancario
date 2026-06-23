# Design — Proveniência de execuções em SQLite

**Data:** 2026-06-23
**Status:** Aprovado (brainstorming)

## Objetivo

Registrar metadados de cada execução do extrator de extratos bancários em um
banco SQLite local, para apoiar a depuração ao longo do tempo: quando rodou,
qual versão do código gerou o resultado, quantos arquivos foram processados,
quais tiveram erro. O Excel continua sendo a saída principal de dados; o SQLite
é histórico de proveniência.

## Decisões

- **SQLite local via biblioteca nativa `sqlite3`** — sem Docker, sem dependências
  novas. (SQLite é um banco em arquivo embutido; containerizá-lo agrega
  complexidade de volumes/locking sem benefício para um script local.)
- **Arquivo do banco:** `Data/proveniencia.db`, criado automaticamente na 1ª
  execução com `CREATE TABLE IF NOT EXISTS`.
- **`Data/*.db` adicionado ao `.gitignore`** — o banco é histórico de runs, não
  código-fonte.
- **Módulo isolado** `src/core/proveniencia.py` com uma classe `Proveniencia`
  que encapsula a conexão e os inserts. Nenhum SQL espalhado pelo restante do
  código.
- **Versão do código** capturada automaticamente do git (hash do commit +
  flag de alterações não commitadas).
- **Detalhes de erro permanecem na aba "Erros" do Excel.** No SQLite guardamos
  apenas a contagem de erros por arquivo.

## Esquema

### Tabela `execucao` (1 linha por run do `main.py`)

| coluna | tipo | descrição |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | identificador da execução |
| `inicio` | TEXT | timestamp ISO 8601 do início |
| `fim` | TEXT | timestamp ISO 8601 do fim (preenchido ao finalizar) |
| `duracao_segundos` | REAL | tempo total da execução |
| `git_commit` | TEXT | hash do commit atual (`"indisponivel"` se git falhar) |
| `git_sujo` | INTEGER | 1 se há alterações não commitadas, 0 caso contrário |
| `versao_python` | TEXT | ex.: `3.10.11` |
| `diretorio_input` | TEXT | pasta de PDFs lida |
| `arquivo_saida` | TEXT | caminho do `.xlsx` gerado |
| `total_arquivos` | INTEGER | PDFs encontrados no diretório |
| `total_sucesso` | INTEGER | PDFs processados sem nenhum erro |
| `total_com_erro` | INTEGER | PDFs com ≥1 erro |
| `total_registros` | INTEGER | linhas de movimentação extraídas no run |
| `status` | TEXT | `SUCESSO` / `SUCESSO_PARCIAL` / `FALHA` |
| `mensagem_erro` | TEXT | preenchido só se o run inteiro quebrar (nullable) |

### Tabela `arquivo_processado` (1 linha por PDF)

| coluna | tipo | descrição |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | identificador do arquivo processado |
| `execucao_id` | INTEGER | FK → `execucao.id` |
| `nome_arquivo` | TEXT | nome do PDF |
| `banco` | TEXT | BB / CEF (CAIXA) / BANCO_DESCONHECIDO |
| `template` | TEXT | template detectado |
| `total_paginas` | INTEGER | páginas do PDF |
| `total_registros` | INTEGER | movimentações extraídas desse arquivo |
| `total_erros` | INTEGER | erros nesse arquivo |
| `status` | TEXT | `SUCESSO` / `PARCIAL` / `FALHA` / `TEMPLATE_DESCONHECIDO` / `IMAGEM` |
| `processado_em` | TEXT | timestamp ISO 8601 |

**Status derivado:**
- `arquivo_processado.status`: `SUCESSO` se `total_erros == 0` e houve registros;
  `PARCIAL` se houve registros e erros; `FALHA` se o PDF lançou exceção antes de
  processar; `TEMPLATE_DESCONHECIDO` e `IMAGEM` para os casos já existentes.
- `execucao.status`: `SUCESSO` se nenhum arquivo com erro; `SUCESSO_PARCIAL` se
  parte dos arquivos teve erro; `FALHA` se o run inteiro quebrou.

## Componentes e interfaces

### `src/core/proveniencia.py` — classe `Proveniencia`

Responsabilidade única: persistir proveniência no SQLite. Não conhece pdfplumber
nem openpyxl.

- `__init__(self, caminho_db)` — abre conexão e garante o schema.
- `iniciar_execucao(self, diretorio_input, arquivo_saida, total_arquivos) -> int`
  — insere linha em `execucao` com `inicio`, dados de git, versão do Python;
  retorna `execucao_id`.
- `registrar_arquivo(self, execucao_id, nome_arquivo, banco, template,
  total_paginas, total_registros, total_erros, status)` — insere em
  `arquivo_processado`.
- `finalizar_execucao(self, execucao_id, fim, duracao, totais..., status,
  mensagem_erro=None)` — atualiza a linha da execução com os agregados finais.
- `fechar(self)` — fecha a conexão.

Helper interno `_info_git()` → `(commit, sujo)` via `subprocess` em `try/except`;
se git indisponível, retorna `("indisponivel", 0)`.

### Integração

- `src/main.py`: instancia `Proveniencia`, chama `iniciar_execucao` antes da
  extração e `finalizar_execucao` num bloco `try/finally` (registra mesmo em
  caso de exceção do run).
  - **Correção de passagem:** os caminhos fixos de input/output (hoje apontando
    para `C:\Users\jpez1\...`) passam a ser derivados da raiz do projeto via
    `pathlib.Path(__file__)`, funcionando em qualquer máquina. O `.db` de
    proveniência usa a mesma raiz (`Data/proveniencia.db`).
- `src/core/exctract_data.py`: `extract_pdfs` recebe o objeto `prov` e o
  `execucao_id`, e chama `prov.registrar_arquivo(...)` ao terminar cada PDF,
  usando os contadores que o loop já calcula (páginas, registros, erros). Também
  acumula os totais que o `main.py` passará para `finalizar_execucao`.

## Tratamento de erros

**Regra de ouro: a proveniência nunca derruba a extração.** Toda escrita no
SQLite é protegida; se o banco falhar, loga um aviso (`print`) e a execução
segue. O Excel permanece como saída principal.

## Testes (TDD)

`proveniencia.py` testado isoladamente com um `.db` temporário:
- criação do schema (tabelas existem após `__init__`);
- `iniciar_execucao` insere e retorna id válido;
- `registrar_arquivo` insere linha vinculada à execução;
- `finalizar_execucao` atualiza agregados e status;
- caso de git indisponível grava `"indisponivel"` sem lançar exceção.

## No escopo (correção de passagem)

- Substituir os caminhos absolutos fixos em `src/main.py` por caminhos relativos
  à raiz do projeto (`pathlib.Path`), para o sistema rodar em qualquer máquina.

## Fora de escopo

- Migração de schema / versionamento do banco (CREATE IF NOT EXISTS basta agora).
- Interface de consulta/relatório sobre o banco.
- Mover detalhes de erro do Excel para o SQLite.
