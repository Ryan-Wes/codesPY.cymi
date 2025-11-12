import fitz  # PyMuPDF
import os
import re

# Caminho da pasta com os PDFs
pasta_pdfs = r"C:\Users\wrlopesr\Downloads\Levante - L102-20250801T134623Z-1-001\Levante - L102\Levante - L102"
saida_arquivo = os.path.join(pasta_pdfs, "resultado.txt")

# Expressões regulares robustas
regex_torre = re.compile(r"\b0*(\d{1,3})\s*/\s*0*(\d{1,2})\b")  # normaliza 06/4 → 6/4
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
                    torre_id = f"{int(match.group(1))}/{int(match.group(2))}"
                    if torre_id not in dados_torres:
                        # bloco maior para varredura
                        inicio = max(0, i - 10)
                        fim = min(len(linhas), i + 40)
                        bloco = "\n".join(linhas[inicio:fim])

                        x = regex_x.search(bloco)
                        y = regex_y.search(bloco)
                        ele = regex_ele.search(bloco)
                        angulo = regex_angulo.search(bloco)

                        # só salva se tiver ao menos X, Y e ele
                        if x and y and ele:
                            dados_torres[torre_id] = {
                                "X": x.group(1),
                                "Y": y.group(1),
                                "ele": ele.group(1),
                                "line_angle": angulo.group(1) if angulo else "---"
                            }

            # ordena por número real da torre
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
