

def identificador_template(text):
    
    lines = text.upper().splitlines()


    for i, line in enumerate(lines):
        # ============== BB (BANCO DO BRASIL) ======================
        if ("LANÇAMENTOS") in line:

            next_lineBB = lines[i+1] if i < len(lines) else ""

            if ("DT. BALANCETE" in next_lineBB and
                "DT. MOVIMENTO" in next_lineBB and
                "HISTÓRICO" in next_lineBB and
                "DOCUMENTO" in next_lineBB and
                "VALOR" in next_lineBB and
                "SALDO" in next_lineBB
                ):
                banco = "BB"
                return "BB_TEMPLATE_1", banco
            
            # ============== TEMPLATE 2 ======================


            if ("DT.") in next_lineBB:

                next2lines = lines[i+2] if i < len(lines) else ""

                # ============== TEMPLATE 2 ======================
                if ("AG. ORIGEM" in next2lines and
                    "LOTE" in next2lines and
                    "HISTÓRICO" in next2lines and
                    "DOCUMENTO" in next2lines and
                    "VALOR" in next2lines and
                    "SALDO" in next2lines):
                    banco = "BB"
                    return "BB_TEMPLATE_2", banco
        
        # ============== CEF (CAIXA) ======================
        if (
        "PERÍODO" in line and
        "DE:" in line and
        "ATÉ:" in line
        ):
            next_lineCEF = lines[i+1] if i < len(lines) else ""

            if (
                "DATA MOV" in next_lineCEF and
                "NR. DOC." in next_lineCEF and
                "HISTÓRICO" in next_lineCEF and
                "VALOR" in next_lineCEF and
                "SALDO" in next_lineCEF 
            ):
                banco = "CEF (CAIXA)"
                return "CEF_TEMPLATE_1", banco
        

    return "TEMPLATE_DESCONHECIDO", "BANCO_DESCONHECIDO"



        
