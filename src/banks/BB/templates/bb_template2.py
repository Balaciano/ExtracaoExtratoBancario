import re


def bb_template2(lines, pdf_records, banco, file, page_num, data_pattern, valor_pattern, conta_corrente):
    dentro_bloco = False
    cc = None
    transacao_num = 0

    for i, line in enumerate(lines):
        registro = {}

        #print(line)
        
        if "AGÊNCIA" in line.upper():
            dentro_bloco = True

        if dentro_bloco:
            if "Conta corrente" in line:
                cc = re.search(r"(\d{4,}-\d)", line)
                if cc:
                    conta_corrente[0] = cc.group(1)
        
        if "EXTRATO" in line.upper():
            dentro_bloco = False
        
            
        line = line.replace("?", "")
    
        #Data sem hora
        data = re.match(r"^\d{2}/\d{2}/\d{4}(?!,)(?!\s+\d{2}:\d{2}:\d{2})", line)


        if data:
            achou = True
            registro["Data"] = data.group()

            saldo_completo = None
            valor_match = None


            if "SALDO ANTERIOR" in line.upper() or "S A L D O" in line:
                transacao_num+=1

                valores = list(re.finditer(r"\d[\d.]*,\d{2}\s*[DC]?", line))
            

                if valores:
                    if len(valores) == 2:
                        saldo_completo = valores[-1].group()

                        valor_match = valores[-2]

                    elif len(valores) == 1:
                        saldo_completo = valores[-1].group()

                    if saldo_completo:
                        tipo_saldo = re.search(r"[DC]$", saldo_completo)
                        registro["D/C Saldo"] = tipo_saldo.group() if tipo_saldo else ""
                        saldo_final = re.sub(r"[DC]$", "", saldo_completo)
                        registro["Saldo"] = saldo_final

                    if valor_match:
                        valor_completo = valor_match.group().strip()

                        tipo_valor = re.search(r"[DC]$", valor_completo)
                        registro["D/C Valor"] = tipo_valor.group() if tipo_valor else ""

                        valor_final = re.sub(r"[DC]$", "", valor_completo)
                        registro["Valor"] = valor_final
                    

                pdf_records.append([
                    registro.get("Data"),
                    conta_corrente[0],
                    "Saldo Anterior",
                    None,
                    registro.get("Valor"),
                    registro.get("D/C Valor"),
                    registro.get("Saldo"),
                    registro.get("D/C Saldo"),
                    banco,
                    file,
                    page_num,
                    transacao_num,
                    "BB Template 2"
                ])

            else:
                transacao_num+=1
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


                valor_inicio = valor_match.start()

                antes_valor = line[:valor_inicio].strip().split()

                documento = None
                for token in reversed(antes_valor):
                    if re.fullmatch(r"\d+(\.\d+)*", token):
                        documento = token
                        break

                registro["Dcto"] = documento

                historico = ""
                if documento:
                    antes_doc = pos_data.rfind(documento)

                    historico = pos_data[:antes_doc].strip()

                    next_line = lines[i+1] if i+1 < len(lines) else ""

                    if not re.match(data_pattern, next_line) and not "http" in next_line:

                        historico += " " + next_line.strip()

                    registro["Histórico"] = historico
                else:

                    next_line = lines[i+1] if i+1 < len(lines) else ""

                    if not re.match(data_pattern, next_line) and not "http" in next_line:

                        historico += " " + next_line.strip()

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
                    "BB Template 2"
                ])
