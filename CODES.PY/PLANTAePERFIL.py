import fitz  # PyMuPDF
import os
import re

pasta_pdfs = r"C:\Users\wrlopesr\Downloads\Levante - L102-20250801T134623Z-1-001\Levante - L102\Levante - L102"
saida_arquivo = os.path.join(pasta_pdfs, "resultado.txt")

# Regex padrão
regex_torre = re.compile(r"(\d{3}\s*/\s*\d)")
regex_x = re.compile(r"X=\s*([\d.,]+)")
regex_y = re.compile(r"Y=\s*([\d.,]+)")
regex_ele = re.compile(r"ele=\s*([\d.,]+)")
regex_angle = re.compile(r"line angle=\s*([^\n\r]+)")

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

                torres_dict = {}

                for pagina in doc:
                    blocos = pagina.get_text("blocks")  # pega blocos estruturados (x, y, w, h, text, etc.)

                    for _, _, _, _, texto, *_ in blocos:
                        if "X=" in texto and "Y=" in texto and "ele=" in texto:
                            torre_match = regex_torre.search(texto)
                            if torre_match:
                                torre = torre_match.group(1).replace(" ", "")

                                if torre not in torres_dict:
                                    x = regex_x.search(texto)
                                    y = regex_y.search(texto)
                                    ele = regex_ele.search(texto)
                                    ang = regex_angle.search(texto)

                                    torres_dict[torre] = {
                                        "X": x.group(1) if x else "---",
                                        "Y": y.group(1) if y else "---",
                                        "ele": ele.group(1) if ele else "---",
                                        "angle": ang.group(1) if ang else "---"
                                    }

                # Ordenar e escrever
                for torre in sorted(torres_dict.keys(), key=lambda x: [int(n) for n in x.split("/")]):
                    d = torres_dict[torre]
                    saida.write(f"Torre: {torre}\n")
                    saida.write(f"X={d['X']}\n")
                    saida.write(f"Y={d['Y']}\n")
                    saida.write(f"ele={d['ele']}\n")
                    saida.write(f"line angle={d['angle']}\n")
                    saida.write("---\n")

                doc.close()

            except Exception as e:
                arquivos_com_erro.append((nome_arquivo, str(e)))

print(f"\n✅ PDFs analisados com sucesso: {arquivos_lidos} de 11")
if arquivos_com_erro:
    print("⚠️ Arquivos com erro:")
    for arq, erro in arquivos_com_erro:
        print(f"- {arq}: {erro}")
print(f"\n📝 Resultado salvo em: {saida_arquivo}")
