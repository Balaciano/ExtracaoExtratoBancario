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
