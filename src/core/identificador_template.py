

def identificador_template(text):
    
    lines = text.upper().splitlines()


    for i, line in enumerate(lines):
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
        if (
            "DT. MOVIMENTO" in line and
            "DT. BALANCETE" in line and
            "HISTÓRICO" in line and
            "DOCUMENTO" in line and
            "VALOR" in line and
            "SALDO" in line
        ):
            banco = "BB"
            return "BB_template_1", banco
        
        if (
            "LOTE" in line and
            "AG. ORIGEM" in line and
            "DOCUMENTO" in line and
            "VALOR" in line and
            "SALDO" in line
        ):
            banco = "BB"
            return "BB_template_2", banco
        

    return "TEMPLATE_DESCONHECIDO", "BANCO_DESCONHECIDO"



        
