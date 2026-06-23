import sqlite3
from core.proveniencia import Proveniencia
from core import proveniencia as prov_mod


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


def test_info_git_indisponivel_nao_lanca(monkeypatch):
    def _falha(*args, **kwargs):
        raise FileNotFoundError("git não encontrado")

    monkeypatch.setattr(prov_mod.subprocess, "run", _falha)
    commit, sujo = prov_mod._info_git()
    assert commit == "indisponivel"
    assert sujo == 0
