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
