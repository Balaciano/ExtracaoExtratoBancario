

def identificador_template(text):
    
    lines = text.upper().splitlines()


    for i, line in enumerate(lines):

        if (
            "DATA MOV." in line and
            "NR. DOC." in line and
            "HISTÓRICO" in line and
            "VALOR" in line and
            "SALDO" in line
        ):
            banco = "BancoQUalquer"
            return "BancoQualquer", banco
        

    return "TEMPLATE_DESCONHECIDO", "BANCO_DESCONHECIDO"



        
