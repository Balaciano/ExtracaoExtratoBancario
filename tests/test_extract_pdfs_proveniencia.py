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
