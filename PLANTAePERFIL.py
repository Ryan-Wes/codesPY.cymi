import fitz  # PyMuPDF
import os
import re

# Caminho da pasta com os PDFs
pasta_pdfs = r"C:\Users\wrlopesr\Downloads\Levante - L102-20250801T134623Z-1-001\Levante - L102\Levante - L102"
saida_arquivo = os.path.join(pasta_pdfs, "resultado.txt")

# Expressões regulares ajustadas
regex_torre = re.compile(r"(?:T(?:ORRE)?\s*)?(\d{3}\s*/\s*\d)", re.IGNORECASE)
regex_x = re.compile(r"X=\s*([\d.,]+)")
regex_y = re.compile(r"Y=\s*([\d.,]+)")
regex_ele = re.compile(r"ele=\s*([\d.,]+)")
regex_angulo = re.compile(r"line angle=\s*([^\n\r]+)")

arquivos_lidos = 0
arquivos_com_erro = []

with open(saida_arquivo, "w", encoding="utf-8") as saida:
    for nome_arquivo in sorted(os.listdir(pasta_pdfs)):
        if nome_arquivo.lower().endswith(".pdf"):
            caminho_pdf = os.path.join(pasta_pdfs, nome_arquivo)
            try:
                doc = fitz.open(caminho_pdf)
                arquivos_lidos += 1
                saida.write(f"\n=== {nome_arquivo} ===\n")

                texto_total = ""
                for pagina in doc:
                    texto_total += pagina.get_text()

                linhas = texto_total.split("\n")
                torres_dict = {}

                for i, linha in enumerate(linhas):
                    match = regex_torre.search(linha)
                    if match:
                        torre_raw = match.group(1).replace(" ", "")  # Ex: "135/1"
                        if torre_raw not in torres_dict:
                            bloco = "\n".join(linhas[i:i+40])  # ← AUMENTADO

                            x = regex_x.search(bloco)
                            y = regex_y.search(bloco)
                            ele = regex_ele.search(bloco)
                            angulo = regex_angulo.search(bloco)

                            # Se nenhum dado foi extraído, não salva ainda
                            if any([x, y, ele, angulo]):
                                torres_dict[torre_raw] = {
                                    "X": x.group(1) if x else "---",
                                    "Y": y.group(1) if y else "---",
                                    "ele": ele.group(1) if ele else "---",
                                    "angle": angulo.group(1) if angulo else "---"
                                }

                for torre in sorted(torres_dict.keys(), key=lambda x: [int(n) for n in x.split("/")]):
                    dados = torres_dict[torre]
                    saida.write(f"Torre: {torre}\n")
                    saida.write(f"X={dados['X']}\n")
                    saida.write(f"Y={dados['Y']}\n")
                    saida.write(f"ele={dados['ele']}\n")
                    saida.write(f"line angle={dados['angle']}\n")
                    saida.write("---\n")

                doc.close()
            except Exception as e:
                arquivos_com_erro.append((nome_arquivo, str(e)))

# Feedback final
print(f"\n✅ PDFs analisados com sucesso: {arquivos_lidos} de 11")
if arquivos_com_erro:
    print("⚠️ Alguns arquivos deram erro:")
    for arq, erro in arquivos_com_erro:
        print(f"- {arq}: {erro}")
print(f"\n📝 Resultado salvo em: {saida_arquivo}")
