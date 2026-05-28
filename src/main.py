import time 
import os
from pathlib import Path
from openpyxl import Workbook, load_workbook
from core.exctract_data import extract_pdfs
import sys

sys.stdout.reconfigure(encoding='utf-8')


inicio = time.time()

leitura_directory = r"C:\Users\jpez1\OneDrive\Área de Trabalho\Projeto_BD1\Extr-oExtratoBancario\Data\input"

files = os.listdir(leitura_directory)

if not files:
    raise Exception("Nenhum arquivo encontrado nesse diretório")

Excel_Output = Path(
    r"C:\Users\jpez1\OneDrive\Área de Trabalho\Projeto_BD1\Extr-oExtratoBancario\Data\output"
) / "Teste.xlsx"

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
        "Data", "Conta Corrente", "Histórico", "Dcto", "Valor", "D/C Valor", "Saldo", "D/C Saldo", "Banco", "Nome do PDF", "Pagina", "Linha", "Status"
    ])
    ws_erro = wb.create_sheet("Erros")
    ws_erro.append(["Banco", "Arquivo", "Página", "Linha", "Conteúdo", "Erro"])



extract_pdfs(files, leitura_directory, ws)



wb.save(Excel_Output)



fim = time.time()
print(f"Tempo total: {(fim - inicio)/60:.2f} minutos")
