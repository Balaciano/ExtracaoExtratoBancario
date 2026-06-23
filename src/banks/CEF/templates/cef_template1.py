import re
from core.error_excel  import registrar_erro

def cef_template1(lines, pdf_records, banco, file, page_num, data_pattern, valor_pattern, conta_corrente, ws_erro):
    cc = None
    transacao_num = 0

    for i, line in enumerate(lines):
        registro = {}

        if "Conta Referência" in line:
            cc = re.search(r"[^/]+$", line)
            if cc:
                conta_corrente[0] = cc.group(0)

        data = re.match(r"^\d{2}/\d{2}/\d{4}(?!,)(?!\s+\d{2}:\d{2}:\d{2})", line)

        if data:
            try:
                transacao_num+=1
                registro["Data"] = data.group()

                saldo_completo = None
                valor_match = None

                if "Saldo Atualizado" in line:
                    continue

                valores = list(re.finditer(valor_pattern, line))

                if len(valores) >= 1:
                    valor_match = valores[0]

                if len(valores) >= 2:
                    saldo_completo = valores[1].group()

                if saldo_completo:
                    tipo_saldo = re.search(r"[DC]$", saldo_completo)
                    registro["D/C Saldo"] = tipo_saldo.group() if tipo_saldo else ""
                    saldo_final = re.sub(r"[DC]$", "", saldo_completo)
                    registro["Saldo"] = saldo_final

                if valor_match:
                    valor_completo = valor_match.group().strip()

                    tipo = re.search(r"[DC]$", valor_completo)
                    registro["D/C Valor"] = tipo.group() if tipo else ""

                    valor_final = re.sub(r"[DC]$", "", valor_completo)
                    registro["Valor"] = valor_final


                pos_data = line[data.end():].strip()

                match = re.match(r"^(\d+)\s+(.*)", pos_data)

                if match:
                    numero_doc = match.group(1)
                    resto = match.group(2)
                else:
                    numero_doc = ""
                    resto = pos_data

                registro["Dcto"] = numero_doc

                valores = list(re.finditer(valor_pattern, resto))

                if valores:
                    primeiro_valor_inicio = valores[0].start()
                    historico = resto[:primeiro_valor_inicio].strip()
                else:
                    historico = resto

                registro["Histórico"] = historico
            
                pdf_records.append([
                        registro.get("Data"),
                        conta_corrente[0],
                        registro.get("Histórico"),
                        registro.get("Dcto"),
                        registro.get("Valor"),
                        registro.get("D/C Valor"),
                        registro.get("Saldo"),
                        registro.get("D/C Saldo"), 
                        banco,
                        file,
                        page_num,
                        transacao_num,
                        "CEF Template 1"
                    ])
            except Exception as e:
                print(f"Erro na linha de transacao {transacao_num}:{e}")
                registrar_erro(
                    ws_erro,
                    banco,
                    file,
                    page_num,
                    transacao_num,
                    line,
                    e
                )
                pdf_records.append([
                    None,                               
                    conta_corrente[0],                  
                    "ERRO PROCESSAMENTO",                                   None,                               
                    None,                               
                    None,                               
                    None,                               
                    None,                               
                    banco,
                    file,
                    page_num,
                    transacao_num,
                    "ERRO",
                    line
                ])