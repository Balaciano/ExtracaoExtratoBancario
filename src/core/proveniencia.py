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
        self.caminho_db = str(caminho_db)
        self.conn = sqlite3.connect(self.caminho_db)
        self._criar_schema()
        print(f"[proveniencia] banco pronto em: {self.caminho_db}")

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
        print(
            f"[proveniencia] execucao #{cur.lastrowid} registrada no banco "
            f"(inicio) - {total_arquivos} arquivo(s) a processar"
        )
        return cur.lastrowid

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
        print(
            f"[proveniencia] arquivo '{nome_arquivo}' gravado no banco "
            f"(execucao #{execucao_id}) - {status}: "
            f"{total_registros} registro(s), {total_erros} erro(s)"
        )

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
        print(
            f"[proveniencia] execucao #{execucao_id} finalizada no banco - "
            f"{status} ({total_sucesso} sucesso, {total_com_erro} com erro, "
            f"{total_registros} registro(s))"
        )

    def fechar(self):
        self.conn.close()
