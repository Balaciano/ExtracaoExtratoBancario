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
