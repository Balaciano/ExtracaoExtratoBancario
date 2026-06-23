def registrar_erro(
    ws_erro,
    banco,
    arquivo,
    pagina,
    linha,
    conteudo,
    erro
):
    ws_erro.append([
        banco,
        arquivo,
        pagina,
        linha,
        conteudo,
        str(erro)
    ])