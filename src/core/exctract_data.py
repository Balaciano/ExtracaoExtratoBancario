import pdfplumber
from openpyxl import Workbook, load_workbook
from core.identificador_template import identificador_template
from banks.BB.templates.bb_template1 import bb_template1
from banks.BB.templates.bb_template2 import bb_template2


def extract_pdfs(files, directory, ws):
    

    print(len(files))
    count_pdf = 0


    for file in files:
        pdf_records = []
           

        conta_corrente = [None]
        
        count_pdf +=1
        print(count_pdf, '/',len(files) , file)

        with pdfplumber.open(directory + "/" + file) as pdf:
        

            for page_num, page in enumerate(pdf.pages, start=1):
            
                print(f"Processando página {page_num}/{len(pdf.pages)}")
                
                text = page.extract_text()
                tables = page.extract_tables()
                
                
                if page_num == 1:
                    template_arquivo, banco_arquivo = identificador_template(text)

                template = template_arquivo
                banco = banco_arquivo

                if not text or not text.strip():
                    ws.append([
                        None, None, None,None,None, None, None, file, page_num, None, "IMAGEM"
                    ])
                    continue

                lines = text.splitlines()


                achou = False
                registro = {}
                erro = None
                
                data_pattern = r"^(\d{2}/\d{2}/\d{4})"
                valor_pattern = r"\d{1,3}(?:\.\d{3})*,\d{2}\s*[DC]?"


                if template == "BB_TEMPLATE_1":
                    bb_template1(lines, pdf_records, banco, file, page_num, data_pattern, valor_pattern, conta_corrente)

                if template == "BB_TEMPLATE_2":
                    bb_template2(lines, pdf_records, banco, file, page_num, data_pattern, valor_pattern, conta_corrente)

            for registro in pdf_records:
                ws.append(registro)
    