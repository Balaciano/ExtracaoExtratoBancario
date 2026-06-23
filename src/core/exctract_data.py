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
