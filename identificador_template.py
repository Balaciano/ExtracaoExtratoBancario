

def identificador_template(text):
    
    lines = text.upper().splitlines()


    for i, line in enumerate(lines):

        # =================================== BANCO CEF/CAIXA ==============================
        # ============== TEMPLATE 1 ======================
        
        if (
            "DATA MOV." in line and
            "NR. DOC." in line and
            "HISTÓRICO" in line and
            "VALOR" in line and
            "SALDO" in line
        ):
            banco = "CEF"
            return "CEF_TEMPLATE_1", banco
        

        # ============== TEMPLATE 2 ======================

        if ("SALDO ANTERIOR AO PERÍODO SOLICITADO" in line):

            proxima_linha = lines[i+1] if i < len(lines) else ""
            
            if ("EXTRATO NO PERÍODO DE" in proxima_linha):

                proxima2_linha = lines[i+4]

                if ("DATA EFETIVA" in proxima2_linha):

                    banco = "CEF"
                    return "CEF_TEMPLATE_2", banco
                
        # =================================== BANCO DO BRASIL (BB) ==============================
        # ============== TEMPLATE 1 ======================
        if ("LANÇAMENTOS") in line:

            next_lineBB = lines[i+1] if i < len(lines) else ""

            if ("DT. BALANCETE" in next_lineBB and
                "DT. MOVIMENTO" in next_lineBB and
                "AG. ORIGEM" in next_lineBB and
                "LOTE" in next_lineBB and
                "HISTÓRICO" in next_lineBB and
                "DOCUMENTO" in next_lineBB and
                "VALOR" in next_lineBB and
                "SALDO" in next_lineBB
                ):
                banco = "BB"
                return "BB_TEMPLATE_1", banco
            
            # ============== TEMPLATE 1 e 2 ======================

            if ("DT.") in next_lineBB:

                next2lines = lines[i+2] if i < len(lines) else ""

                # ============== TEMPLATE 1 ======================
                if ("AG. ORIGEM" in next2lines and
                    "LOTE" in next2lines and
                    "HISTÓRICO" in next2lines and
                    "DOCUMENTO" in next2lines and
                    "VALOR" in next2lines and
                    "SALDO" in next2lines):
                    banco = "BB"
                    return "BB_TEMPLATE_1", banco
            
                # ============== TEMPLATE 2 ======================
                if (
                    "HISTÓRICO" in next2lines and
                    "DOCUMENTO" in next2lines and
                    "VALOR" in next2lines and
                    "SALDO" in next2lines and
                    "AG. ORIGEM" not in next2lines and
                    "LOTE" not in next2lines
                ):
                    banco = "BB"
                    return "BB_TEMPLATE_2", banco
                
        # =================================== BRADESCO ==============================
        # ============== TEMPLATE 1 ======================
        if (
            "DATA" in line and
            "LANÇAMENTO" in line and
            "DCTO." in line and
            "CRÉDITO" in line and
            "DÉBITO" in line and
            "SALDO" in line
        ):
            before_lineBradesco = lines[i-1]

            if (
                "EXTRATO DE: AG:" in before_lineBradesco and
                "CC" in before_lineBradesco and
                "ENTRE" in before_lineBradesco
            ):
                banco = "Bradesco"
                return "BRADESCO_TEMPLATE_1", banco
            
        # ============== TEMPLATE 2 ======================
        


    return "TEMPLATE_DESCONHECIDO", "BANCO_DESCONHECIDO"



        
