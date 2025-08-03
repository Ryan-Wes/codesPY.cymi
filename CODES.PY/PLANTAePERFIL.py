import fitz  # PyMuPDF
import os
import re

# Caminho da pasta com os PDFs
pasta_pdfs = r"C:\Users\wrlopesr\Downloads\Levante - L102-20250801T134623Z-1-001\Levante - L102\Levante - L102"
saida_arquivo = os.path.join(pasta_pdfs, "resultado.txt")

# Expressões regulares ajustadas
regex_torre = re.compile(r"(\d{1,3}\s*/\s*\d)")  # agora aceita ex: 0/1, 12/2, 135/1
regex_x = re.compile(r"X=\s*([\d.,]+)")
regex_y = re.compile(r"Y=\s*([\d.,]+)")
regex_ele = re.compile(r"ele=\s*([\d.,]+)")
regex_angulo = re.compile(r"line angle=\s*([^\n\r]+)")

with open(saida_arquivo, "w", encoding="utf-8") as saida:
    arquivos_processados = 0

    for nome_arquivo in sorted(os.listdir(pasta_pdfs)):
        if nome_arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(pasta_pdfs, nome_arquivo)
            saida.write(f"\n=== {nome_arquivo} ===\n")
            arquivos_processados += 1

            doc = fitz.open(caminho_pdf)
            texto_total = ""
            for pagina in doc:
                texto_total += pagina.get_text()

            linhas = texto_total.split("\n")
            dados_torres = {}

            for i, linha in enumerate(linhas):
                match = regex_torre.search(linha)
                if match:
                    torre_raw = match.group(1).replace(" ", "")
                    if torre_raw not in dados_torres:
                        bloco = "\n".join(linhas[i:i+20])
                        x = regex_x.search(bloco)
                        y = regex_y.search(bloco)
                        ele = regex_ele.search(bloco)
                        angulo = regex_angulo.search(bloco)

                        dados_torres[torre_raw] = {
                            "X": x.group(1) if x else "---",
                            "Y": y.group(1) if y else "---",
                            "ele": ele.group(1) if ele else "---",
                            "line_angle": angulo.group(1) if angulo else "---"
                        }

            # Ordenar torres numericamente por prefixo/sufixo
            def ordena_chave(t):
                try:
                    parte = t.split("/")
                    return (int(parte[0]), int(parte[1]))
                except:
                    return (999, 999)

            for torre in sorted(dados_torres.keys(), key=ordena_chave):
                info = dados_torres[torre]
                saida.write(f"Torre: {torre}\n")
                saida.write(f"X={info['X']}\n")
                saida.write(f"Y={info['Y']}\n")
                saida.write(f"ele={info['ele']}\n")
                saida.write(f"line angle={info['line_angle']}\n")
                saida.write("---\n")

            doc.close()

print(f"\n✅ PDFs analisados com sucesso: {arquivos_processados} de {arquivos_processados}")
print(f"\n📝 Resultado salvo em: {saida_arquivo}")
