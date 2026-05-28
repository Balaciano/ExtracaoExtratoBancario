

def identificador_template(text):
    
    lines = text.upper().splitlines()


    for i, line in enumerate(lines):

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
        

    return "TEMPLATE_DESCONHECIDO", "BANCO_DESCONHECIDO"



        
