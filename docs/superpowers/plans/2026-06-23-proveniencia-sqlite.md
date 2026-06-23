# Proveniência de execuções em SQLite — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Registrar metadados de proveniência de cada execução do extrator de extratos bancários em um SQLite local (`Data/proveniencia.db`), sem derrubar a extração.

**Architecture:** Um módulo isolado `src/core/proveniencia.py` com a classe `Proveniencia` encapsula toda a conexão e SQL. `main.py` controla o ciclo de vida (início/fim) e `exctract_data.py` registra um resumo por PDF. Os detalhes de erro continuam na aba "Erros" do Excel; o SQLite guarda agregados.

**Tech Stack:** Python 3.13 (venv), biblioteca nativa `sqlite3`, `subprocess` (info git), `platform` (versão Python). Testes com `pytest`.

## Global Constraints

- **Sem dependências novas de runtime** — apenas stdlib (`sqlite3`, `subprocess`, `platform`, `datetime`, `pathlib`). `pytest` é dependência só de desenvolvimento.
- **Regra de ouro:** nenhuma falha de proveniência pode interromper a extração. Toda chamada à `Proveniencia` feita a partir de `main.py`/`exctract_data.py` é protegida por `try/except` que apenas loga (`print`) e segue.
- **Banco:** `Data/proveniencia.db`, criado com `CREATE TABLE IF NOT EXISTS`.
- **Timestamps:** ISO 8601 via `datetime.now().isoformat(timespec="seconds")`.
- **Python interpreter dos comandos:** `.venv/Scripts/python.exe` (Windows).
- **Imports do projeto:** o código de runtime roda com `src/` na raiz de import (ex.: `from core.proveniencia import Proveniencia`). Os testes adicionam `src/` ao `sys.path` via `tests/conftest.py`.

---

## File Structure

- **Create** `src/core/proveniencia.py` — classe `Proveniencia` (conexão, schema, inserts/updates) + helper `_info_git`.
- **Create** `tests/conftest.py` — coloca `src/` no `sys.path`.
- **Create** `tests/test_proveniencia.py` — testes unitários da classe.
- **Create** `tests/test_extract_pdfs_proveniencia.py` — teste de integração do registro por arquivo.
- **Create** `.gitignore` — ignora `Data/*.db`, `__pycache__/`, `*.pyc`.
- **Create** `requirements-dev.txt` — `pytest`.
- **Modify** `src/core/exctract_data.py` — nova assinatura `extract_pdfs(..., prov, execucao_id)`, contadores por arquivo, registro por PDF, retorno de agregados.
- **Modify** `src/main.py` — caminhos relativos à raiz do projeto + ciclo de vida da proveniência.

---

### Task 1: Scaffolding de testes + schema da `Proveniencia`

**Files:**
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `tests/conftest.py`
- Create: `src/core/proveniencia.py`
- Test: `tests/test_proveniencia.py`

**Interfaces:**
- Produces: `class Proveniencia` com `__init__(self, caminho_db)` que abre a conexão SQLite e cria o schema; `fechar(self)` que fecha a conexão. Tabelas `execucao` e `arquivo_processado` conforme a spec.

- [ ] **Step 1: Instalar pytest e criar arquivos de scaffolding**

`requirements-dev.txt`:
```
pytest
```

`.gitignore`:
```
__pycache__/
*.pyc
.venv/
Data/*.db
```

`tests/conftest.py`:
```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
```

Instale o pytest:
```bash
.venv/Scripts/python.exe -m pip install pytest
```
Expected: termina com "Successfully installed pytest-...".

- [ ] **Step 2: Escrever o teste que falha (schema)**

`tests/test_proveniencia.py`:
```python
import sqlite3
from core.proveniencia import Proveniencia


def _tabelas(caminho_db):
    conn = sqlite3.connect(str(caminho_db))
    nomes = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    conn.close()
    return nomes


def test_init_cria_schema(tmp_path):
    db = tmp_path / "prov.db"
    prov = Proveniencia(db)
    prov.fechar()

    tabelas = _tabelas(db)
    assert "execucao" in tabelas
    assert "arquivo_processado" in tabelas
```

- [ ] **Step 3: Rodar o teste e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_init_cria_schema -v`
Expected: FAIL com `ModuleNotFoundError: No module named 'core.proveniencia'`.

- [ ] **Step 4: Implementar `Proveniencia` mínima (conexão + schema)**

`src/core/proveniencia.py`:
```python
import sqlite3
import subprocess
import platform
from datetime import datetime


def _info_git():
    """Retorna (commit, sujo). Nunca lança: se git falhar, ('indisponivel', 0)."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
        return commit, (1 if status else 0)
    except Exception:
        return "indisponivel", 0


class Proveniencia:
    def __init__(self, caminho_db):
        self.conn = sqlite3.connect(str(caminho_db))
        self._criar_schema()

    def _criar_schema(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS execucao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inicio TEXT,
                fim TEXT,
                duracao_segundos REAL,
                git_commit TEXT,
                git_sujo INTEGER,
                versao_python TEXT,
                diretorio_input TEXT,
                arquivo_saida TEXT,
                total_arquivos INTEGER,
                total_sucesso INTEGER,
                total_com_erro INTEGER,
                total_registros INTEGER,
                status TEXT,
                mensagem_erro TEXT
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS arquivo_processado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execucao_id INTEGER,
                nome_arquivo TEXT,
                banco TEXT,
                template TEXT,
                total_paginas INTEGER,
                total_registros INTEGER,
                total_erros INTEGER,
                status TEXT,
                processado_em TEXT,
                FOREIGN KEY (execucao_id) REFERENCES execucao (id)
            )
            """
        )
        self.conn.commit()

    def fechar(self):
        self.conn.close()
```

- [ ] **Step 5: Rodar o teste e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_init_cria_schema -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .gitignore requirements-dev.txt tests/conftest.py tests/test_proveniencia.py src/core/proveniencia.py
git commit -m "feat: schema SQLite de proveniência (tabelas execucao e arquivo_processado)"
```

---

### Task 2: `iniciar_execucao`

**Files:**
- Modify: `src/core/proveniencia.py`
- Test: `tests/test_proveniencia.py`

**Interfaces:**
- Consumes: `Proveniencia.__init__`, `_info_git`.
- Produces: `iniciar_execucao(self, diretorio_input, arquivo_saida, total_arquivos) -> int` — insere uma linha em `execucao` (com `inicio`, `git_commit`, `git_sujo`, `versao_python`, `diretorio_input`, `arquivo_saida`, `total_arquivos`, `status='EM_ANDAMENTO'`) e retorna o `id` (`lastrowid`).

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tests/test_proveniencia.py`:
```python
def test_iniciar_execucao_insere_e_retorna_id(tmp_path):
    db = tmp_path / "prov.db"
    prov = Proveniencia(db)

    execucao_id = prov.iniciar_execucao(
        diretorio_input="/in",
        arquivo_saida="/out/Teste.xlsx",
        total_arquivos=3,
    )
    prov.fechar()

    assert isinstance(execucao_id, int)

    conn = sqlite3.connect(str(db))
    linha = conn.execute(
        "SELECT diretorio_input, arquivo_saida, total_arquivos, "
        "versao_python, git_commit, inicio, status FROM execucao WHERE id=?",
        (execucao_id,),
    ).fetchone()
    conn.close()

    assert linha[0] == "/in"
    assert linha[1] == "/out/Teste.xlsx"
    assert linha[2] == 3
    assert linha[3]            # versao_python preenchida
    assert linha[4]            # git_commit preenchido (hash ou 'indisponivel')
    assert linha[5]            # inicio preenchido
    assert linha[6] == "EM_ANDAMENTO"
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_iniciar_execucao_insere_e_retorna_id -v`
Expected: FAIL com `AttributeError: 'Proveniencia' object has no attribute 'iniciar_execucao'`.

- [ ] **Step 3: Implementar `iniciar_execucao`**

Adicione o método à classe `Proveniencia` (em `src/core/proveniencia.py`), após `_criar_schema`:
```python
    def iniciar_execucao(self, diretorio_input, arquivo_saida, total_arquivos):
        commit, sujo = _info_git()
        cur = self.conn.execute(
            """
            INSERT INTO execucao (
                inicio, git_commit, git_sujo, versao_python,
                diretorio_input, arquivo_saida, total_arquivos, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                commit,
                sujo,
                platform.python_version(),
                diretorio_input,
                arquivo_saida,
                total_arquivos,
                "EM_ANDAMENTO",
            ),
        )
        self.conn.commit()
        return cur.lastrowid
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_iniciar_execucao_insere_e_retorna_id -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/proveniencia.py tests/test_proveniencia.py
git commit -m "feat: Proveniencia.iniciar_execucao"
```

---

### Task 3: `registrar_arquivo`

**Files:**
- Modify: `src/core/proveniencia.py`
- Test: `tests/test_proveniencia.py`

**Interfaces:**
- Consumes: `iniciar_execucao` (para obter um `execucao_id` válido nos testes).
- Produces: `registrar_arquivo(self, execucao_id, nome_arquivo, banco, template, total_paginas, total_registros, total_erros, status)` — insere uma linha em `arquivo_processado` com `processado_em` preenchido.

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tests/test_proveniencia.py`:
```python
def test_registrar_arquivo_insere_linha(tmp_path):
    db = tmp_path / "prov.db"
    prov = Proveniencia(db)
    execucao_id = prov.iniciar_execucao("/in", "/out.xlsx", 1)

    prov.registrar_arquivo(
        execucao_id=execucao_id,
        nome_arquivo="Caixa2.pdf",
        banco="CEF (CAIXA)",
        template="CEF_TEMPLATE_1",
        total_paginas=2,
        total_registros=40,
        total_erros=1,
        status="PARCIAL",
    )
    prov.fechar()

    conn = sqlite3.connect(str(db))
    linha = conn.execute(
        "SELECT execucao_id, nome_arquivo, banco, template, total_paginas, "
        "total_registros, total_erros, status, processado_em "
        "FROM arquivo_processado WHERE nome_arquivo='Caixa2.pdf'"
    ).fetchone()
    conn.close()

    assert linha[0] == execucao_id
    assert linha[1] == "Caixa2.pdf"
    assert linha[2] == "CEF (CAIXA)"
    assert linha[3] == "CEF_TEMPLATE_1"
    assert linha[4] == 2
    assert linha[5] == 40
    assert linha[6] == 1
    assert linha[7] == "PARCIAL"
    assert linha[8]            # processado_em preenchido
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_registrar_arquivo_insere_linha -v`
Expected: FAIL com `AttributeError: ... 'registrar_arquivo'`.

- [ ] **Step 3: Implementar `registrar_arquivo`**

Adicione à classe `Proveniencia`:
```python
    def registrar_arquivo(self, execucao_id, nome_arquivo, banco, template,
                          total_paginas, total_registros, total_erros, status):
        self.conn.execute(
            """
            INSERT INTO arquivo_processado (
                execucao_id, nome_arquivo, banco, template, total_paginas,
                total_registros, total_erros, status, processado_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execucao_id,
                nome_arquivo,
                banco,
                template,
                total_paginas,
                total_registros,
                total_erros,
                status,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        self.conn.commit()
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_registrar_arquivo_insere_linha -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/core/proveniencia.py tests/test_proveniencia.py
git commit -m "feat: Proveniencia.registrar_arquivo"
```

---

### Task 4: `finalizar_execucao`

**Files:**
- Modify: `src/core/proveniencia.py`
- Test: `tests/test_proveniencia.py`

**Interfaces:**
- Consumes: `iniciar_execucao`.
- Produces: `finalizar_execucao(self, execucao_id, duracao_segundos, total_sucesso, total_com_erro, total_registros, status, mensagem_erro=None)` — faz `UPDATE` na linha da execução preenchendo `fim`, `duracao_segundos`, agregados, `status` e `mensagem_erro`.

- [ ] **Step 1: Escrever o teste que falha**

Acrescente a `tests/test_proveniencia.py`:
```python
def test_finalizar_execucao_atualiza_agregados(tmp_path):
    db = tmp_path / "prov.db"
    prov = Proveniencia(db)
    execucao_id = prov.iniciar_execucao("/in", "/out.xlsx", 2)

    prov.finalizar_execucao(
        execucao_id=execucao_id,
        duracao_segundos=12.5,
        total_sucesso=1,
        total_com_erro=1,
        total_registros=40,
        status="SUCESSO_PARCIAL",
        mensagem_erro=None,
    )
    prov.fechar()

    conn = sqlite3.connect(str(db))
    linha = conn.execute(
        "SELECT fim, duracao_segundos, total_sucesso, total_com_erro, "
        "total_registros, status FROM execucao WHERE id=?",
        (execucao_id,),
    ).fetchone()
    conn.close()

    assert linha[0]            # fim preenchido
    assert linha[1] == 12.5
    assert linha[2] == 1
    assert linha[3] == 1
    assert linha[4] == 40
    assert linha[5] == "SUCESSO_PARCIAL"
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_finalizar_execucao_atualiza_agregados -v`
Expected: FAIL com `AttributeError: ... 'finalizar_execucao'`.

- [ ] **Step 3: Implementar `finalizar_execucao`**

Adicione à classe `Proveniencia`:
```python
    def finalizar_execucao(self, execucao_id, duracao_segundos, total_sucesso,
                           total_com_erro, total_registros, status,
                           mensagem_erro=None):
        self.conn.execute(
            """
            UPDATE execucao
            SET fim = ?, duracao_segundos = ?, total_sucesso = ?,
                total_com_erro = ?, total_registros = ?, status = ?,
                mensagem_erro = ?
            WHERE id = ?
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                duracao_segundos,
                total_sucesso,
                total_com_erro,
                total_registros,
                status,
                mensagem_erro,
                execucao_id,
            ),
        )
        self.conn.commit()
```

- [ ] **Step 4: Rodar e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py::test_finalizar_execucao_atualiza_agregados -v`
Expected: PASS.

- [ ] **Step 5: Teste do caminho git indisponível (sem lançar)**

Acrescente a `tests/test_proveniencia.py`:
```python
from core import proveniencia as prov_mod


def test_info_git_indisponivel_nao_lanca(monkeypatch):
    def _falha(*args, **kwargs):
        raise FileNotFoundError("git não encontrado")

    monkeypatch.setattr(prov_mod.subprocess, "run", _falha)
    commit, sujo = prov_mod._info_git()
    assert commit == "indisponivel"
    assert sujo == 0
```

Run: `.venv/Scripts/python.exe -m pytest tests/test_proveniencia.py -v`
Expected: todos PASS (5 testes).

- [ ] **Step 6: Commit**

```bash
git add src/core/proveniencia.py tests/test_proveniencia.py
git commit -m "feat: Proveniencia.finalizar_execucao + teste git indisponível"
```

---

### Task 5: Integração em `extract_pdfs` (registro por arquivo)

**Files:**
- Modify: `src/core/exctract_data.py`
- Test: `tests/test_extract_pdfs_proveniencia.py`

**Interfaces:**
- Consumes: `Proveniencia.iniciar_execucao`, `Proveniencia.registrar_arquivo`.
- Produces: `extract_pdfs(files, directory, ws, ws_erro, prov, execucao_id) -> dict` com chaves `total_sucesso`, `total_com_erro`, `total_registros`. Para cada PDF chama `prov.registrar_arquivo(...)`. Marcador de linha de erro: helper `_eh_linha_erro(row)` (linha de erro tem `len(row) > 12 and row[12] == "ERRO"`).

- [ ] **Step 1: Escrever o teste de integração que falha**

`tests/test_extract_pdfs_proveniencia.py`:
```python
import sqlite3
from pathlib import Path

from core.proveniencia import Proveniencia
from core.exctract_data import extract_pdfs

RAIZ = Path(__file__).resolve().parent.parent
INPUT_DIR = RAIZ / "Data" / "input"


class WsFake:
    def __init__(self):
        self.linhas = []

    def append(self, linha):
        self.linhas.append(linha)


def test_extract_pdfs_registra_arquivo_e_retorna_agregados(tmp_path):
    db = tmp_path / "prov.db"
    prov = Proveniencia(db)
    execucao_id = prov.iniciar_execucao(str(INPUT_DIR), "/out.xlsx", 1)

    ws = WsFake()
    ws_erro = WsFake()

    resultado = extract_pdfs(
        ["Caixa2.pdf"], str(INPUT_DIR), ws, ws_erro, prov, execucao_id
    )
    prov.fechar()

    assert set(resultado.keys()) == {
        "total_sucesso", "total_com_erro", "total_registros"
    }
    assert resultado["total_sucesso"] + resultado["total_com_erro"] == 1

    conn = sqlite3.connect(str(db))
    linha = conn.execute(
        "SELECT nome_arquivo, banco, template, total_paginas, status "
        "FROM arquivo_processado WHERE execucao_id=?",
        (execucao_id,),
    ).fetchone()
    conn.close()

    assert linha is not None
    assert linha[0] == "Caixa2.pdf"
    assert linha[1] == "CEF (CAIXA)"
    assert linha[2] == "CEF_TEMPLATE_1"
    assert linha[3] >= 1
    assert linha[4] in {"SUCESSO", "PARCIAL", "FALHA", "IMAGEM"}
```

- [ ] **Step 2: Rodar e verificar que falha**

Run: `.venv/Scripts/python.exe -m pytest tests/test_extract_pdfs_proveniencia.py -v`
Expected: FAIL — `extract_pdfs` ainda tem a assinatura antiga (`TypeError: extract_pdfs() takes 4 positional arguments but 6 were given`).

- [ ] **Step 3: Reescrever `extract_pdfs`**

Substitua todo o conteúdo de `src/core/exctract_data.py` por:
```python
import pdfplumber
from core.identificador_template import identificador_template
from banks.BB.templates.bb_template1 import bb_template1
from banks.BB.templates.bb_template2 import bb_template2
from banks.CEF.templates.cef_template1 import cef_template1

from core.error_excel import registrar_erro


def _eh_linha_erro(row):
    """Linhas de erro emitidas pelos templates têm 'ERRO' na posição 12."""
    return len(row) > 12 and row[12] == "ERRO"


def extract_pdfs(files, directory, ws, ws_erro, prov, execucao_id):
    total_sucesso = 0
    total_com_erro = 0
    total_registros_geral = 0

    print(len(files))
    count_pdf = 0

    for file in files:
        pdf_records = []
        conta_corrente = [None]
        count_pdf += 1
        print(count_pdf, '/', len(files), file)

        banco = "BANCO_DESCONHECIDO"
        template = "TEMPLATE_DESCONHECIDO"
        total_paginas = 0
        erros_pagina = 0
        teve_imagem = False

        try:
            with pdfplumber.open(directory + "/" + file) as pdf:
                total_paginas = len(pdf.pages)

                for page_num, page in enumerate(pdf.pages, start=1):
                    print(f"Processando página {page_num}/{len(pdf.pages)}")

                    try:
                        text = page.extract_text()
                        tables = page.extract_tables()

                        if page_num == 1:
                            template_arquivo, banco_arquivo = identificador_template(text)

                        template = template_arquivo
                        banco = banco_arquivo

                        if not text or not text.strip():
                            teve_imagem = True
                            ws.append([
                                None, None, None, None, None, None, None,
                                file, page_num, None, "IMAGEM"
                            ])
                            continue

                        lines = text.splitlines()

                        data_pattern = r"^(\d{2}/\d{2}/\d{4})"
                        valor_pattern = r"\d{1,3}(?:\.\d{3})*,\d{2}\s*[DC]?"

                        if template == "BB_TEMPLATE_1":
                            bb_template1(lines, pdf_records, banco, file, page_num, data_pattern, valor_pattern, conta_corrente, ws_erro)

                        if template == "BB_TEMPLATE_2":
                            bb_template2(lines, pdf_records, banco, file, page_num, data_pattern, valor_pattern, conta_corrente, ws_erro)

                        if template == "CEF_TEMPLATE_1":
                            cef_template1(lines, pdf_records, banco, file, page_num, data_pattern, valor_pattern, conta_corrente, ws_erro)

                        if template == "TEMPLATE_DESCONHECIDO":
                            registrar_erro(ws_erro, banco, file, page_num, None, "Template não identificado", None)
                            erros_pagina += 1
                            continue

                    except Exception as e:
                        registrar_erro(ws_erro, banco, file, page_num, None, None, e)
                        erros_pagina += 1
                        print(f"Erro na pagina {page_num} do PDF {file}: {e}")
                        continue

                    for registro in pdf_records:
                        ws.append(registro)

            # ---- resumo por arquivo (após o with, com o PDF lido com sucesso) ----
            registros = sum(1 for r in pdf_records if not _eh_linha_erro(r))
            erros_inline = sum(1 for r in pdf_records if _eh_linha_erro(r))
            total_erros = erros_inline + erros_pagina

            if template == "TEMPLATE_DESCONHECIDO":
                status_arquivo = "TEMPLATE_DESCONHECIDO"
            elif registros == 0 and teve_imagem:
                status_arquivo = "IMAGEM"
            elif total_erros > 0 and registros > 0:
                status_arquivo = "PARCIAL"
            elif total_erros > 0 and registros == 0:
                status_arquivo = "FALHA"
            else:
                status_arquivo = "SUCESSO"

            total_registros_geral += registros
            if total_erros > 0 or status_arquivo in ("FALHA", "TEMPLATE_DESCONHECIDO"):
                total_com_erro += 1
            else:
                total_sucesso += 1

            try:
                prov.registrar_arquivo(
                    execucao_id, file, banco, template,
                    total_paginas, registros, total_erros, status_arquivo
                )
            except Exception as e:
                print(f"[proveniencia] falha ao registrar arquivo {file}: {e}")

        except Exception as e:
            registrar_erro(ws_erro, None, file, None, None, None, e)
            print(f"{file} com erro: {e}")
            total_com_erro += 1
            try:
                prov.registrar_arquivo(
                    execucao_id, file, banco, template,
                    total_paginas, 0, 1, "FALHA"
                )
            except Exception as e2:
                print(f"[proveniencia] falha ao registrar arquivo {file}: {e2}")
            continue

    return {
        "total_sucesso": total_sucesso,
        "total_com_erro": total_com_erro,
        "total_registros": total_registros_geral,
    }
```

- [ ] **Step 4: Rodar o teste de integração e verificar que passa**

Run: `.venv/Scripts/python.exe -m pytest tests/test_extract_pdfs_proveniencia.py -v`
Expected: PASS.

- [ ] **Step 5: Rodar a suíte inteira**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Expected: todos PASS (6 testes).

- [ ] **Step 6: Commit**

```bash
git add src/core/exctract_data.py tests/test_extract_pdfs_proveniencia.py
git commit -m "feat: registrar resumo de proveniência por PDF em extract_pdfs"
```

---

### Task 6: Wiring em `main.py` (caminhos relativos + ciclo de vida)

**Files:**
- Modify: `src/main.py`

**Interfaces:**
- Consumes: `extract_pdfs(..., prov, execucao_id) -> dict`, `Proveniencia.iniciar_execucao`, `Proveniencia.finalizar_execucao`, `Proveniencia.fechar`.

- [ ] **Step 1: Reescrever `main.py`**

Substitua todo o conteúdo de `src/main.py` por:
```python
import time
import os
import sys
import platform
from pathlib import Path
from openpyxl import Workbook, load_workbook
from core.exctract_data import extract_pdfs
from core.proveniencia import Proveniencia

sys.stdout.reconfigure(encoding='utf-8')

# Raiz do projeto = pasta acima de src/ — funciona em qualquer máquina.
PROJETO_RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = PROJETO_RAIZ / "Data"

leitura_directory = str(DATA_DIR / "input")
Excel_Output = DATA_DIR / "output" / "Teste.xlsx"
caminho_db = DATA_DIR / "proveniencia.db"

inicio = time.time()

files = os.listdir(leitura_directory)

if not files:
    raise Exception("Nenhum arquivo encontrado nesse diretório")

if os.path.exists(Excel_Output):
    wb = load_workbook(Excel_Output)
    ws = wb.active

    if "Erros" in wb.sheetnames:
        ws_erro = wb["Erros"]
    else:
        ws_erro = wb.create_sheet("Erros")
        ws_erro.append(["Banco", "Arquivo", "Página", "Linha", "Conteúdo", "Erro"])
else:
    wb = Workbook()
    ws = wb.active
    ws.title = "Combinado"
    ws.append([
        "Data", "Conta Corrente", "Histórico", "Dcto", "Valor", "D/C Valor",
        "Saldo", "D/C Saldo", "Banco", "Nome do PDF", "Pagina", "Linha", "Status"
    ])
    ws_erro = wb.create_sheet("Erros")
    ws_erro.append(["Banco", "Arquivo", "Página", "Linha", "Conteúdo", "Erro"])

prov = Proveniencia(caminho_db)
execucao_id = None
resultado = {"total_sucesso": 0, "total_com_erro": 0, "total_registros": 0}
status = "FALHA"
mensagem_erro = None

try:
    try:
        execucao_id = prov.iniciar_execucao(leitura_directory, str(Excel_Output), len(files))
    except Exception as e:
        print(f"[proveniencia] falha ao iniciar execução: {e}")

    resultado = extract_pdfs(files, leitura_directory, ws, ws_erro, prov, execucao_id)

    if resultado["total_com_erro"] == 0:
        status = "SUCESSO"
    elif resultado["total_sucesso"] > 0:
        status = "SUCESSO_PARCIAL"
    else:
        status = "FALHA"
except Exception as e:
    mensagem_erro = str(e)
    status = "FALHA"
    raise
finally:
    wb.save(Excel_Output)

    fim = time.time()
    duracao = fim - inicio

    if execucao_id is not None:
        try:
            prov.finalizar_execucao(
                execucao_id, duracao,
                resultado["total_sucesso"], resultado["total_com_erro"],
                resultado["total_registros"], status, mensagem_erro
            )
        except Exception as e:
            print(f"[proveniencia] falha ao finalizar execução: {e}")

    prov.fechar()
    print(f"Tempo total: {duracao/60:.2f} minutos")
```

> Nota: se `iniciar_execucao` falhar, `execucao_id` fica `None`; nesse caso `extract_pdfs` recebe `None` e suas chamadas `prov.registrar_arquivo` ainda rodam, mas se falharem são apenas logadas (não quebram a extração).

- [ ] **Step 2: Rodar `main.py` de ponta a ponta**

Run (a partir de `src/`, como o projeto já roda):
```bash
.venv/Scripts/python.exe src/main.py
```
Expected: imprime o progresso por arquivo e "Tempo total: ... minutos" sem traceback. Gera `Data/output/Teste.xlsx` e `Data/proveniencia.db`.

- [ ] **Step 3: Verificar que o banco foi populado**

Run:
```bash
.venv/Scripts/python.exe -c "import sqlite3; c=sqlite3.connect('Data/proveniencia.db'); print('execucoes:', c.execute('SELECT COUNT(*) FROM execucao').fetchone()[0]); print('arquivos:', c.execute('SELECT COUNT(*) FROM arquivo_processado').fetchone()[0]); print(c.execute('SELECT id, status, total_arquivos, total_sucesso, total_com_erro, total_registros, git_commit, versao_python FROM execucao ORDER BY id DESC LIMIT 1').fetchone())"
```
Expected: `execucoes` ≥ 1, `arquivos` ≥ 1, e a última execução com `status`, totais e `git_commit`/`versao_python` preenchidos.

- [ ] **Step 4: Rodar a suíte de testes completa**

Run: `.venv/Scripts/python.exe -m pytest tests/ -v`
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add src/main.py
git commit -m "feat: caminhos relativos e ciclo de vida da proveniência em main.py"
```

---

## Self-Review

**Cobertura da spec:**
- Stack `sqlite3` local, sem Docker → Task 1. ✓
- `Data/proveniencia.db` + `CREATE IF NOT EXISTS` → Task 1. ✓
- `.gitignore` para `Data/*.db` → Task 1. ✓
- Módulo isolado `proveniencia.py` → Tasks 1–4. ✓
- Tabela `execucao` (todas as colunas, incl. `versao_python`) → Tasks 1, 2, 4. ✓
- Tabela `arquivo_processado` → Tasks 1, 3. ✓
- Versão via git (commit + sujo) → Task 2 (`_info_git`). ✓
- Detalhes de erro só no Excel; SQLite só contagem → Task 5. ✓
- Status derivados → Task 5. ✓
- Regra de ouro (proveniência não derruba extração) → Tasks 5 e 6 (try/except nas chamadas). ✓
- Integração main/extract → Tasks 5, 6. ✓
- Caminhos relativos (correção de passagem) → Task 6. ✓
- Testes TDD incl. git indisponível → Tasks 1–5. ✓

**Placeholders:** nenhum — todo passo tem código/comando concreto.

**Consistência de tipos:** assinatura `extract_pdfs(files, directory, ws, ws_erro, prov, execucao_id) -> dict` idêntica em Tasks 5 e 6; `Proveniencia.iniciar_execucao/registrar_arquivo/finalizar_execucao/fechar` com as mesmas assinaturas em definição (Tasks 2–4) e uso (Tasks 5–6); chaves do dict de retorno (`total_sucesso`, `total_com_erro`, `total_registros`) consistentes.

## Observação fora de escopo (sinalizada, não corrigida)

Em `exctract_data.py`, o bloco `for registro in pdf_records: ws.append(registro)` roda **dentro** do loop de páginas, e `pdf_records` só é zerado por arquivo. Em PDFs de múltiplas páginas isso reanexa os registros das páginas anteriores ao Excel (duplicação). A proveniência **não** é afetada (conta a partir de `pdf_records`, não do `ws`), por isso o plano preserva o comportamento atual. Recomendo tratar essa duplicação num trabalho separado.
