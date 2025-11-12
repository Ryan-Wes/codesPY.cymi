import os
import re
from collections import Counter
import pytesseract
import fitz  # PyMuPDF
from PIL import Image

# Configuração do caminho do Tesseract OCR no seu PC
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\wrlopesr\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Pasta onde estão os PDFs
PASTA_PDFS = r"C:\Users\wrlopesr\OneDrive - CYMI CONSTRUÇÕES E PARTICIPAÇÕES S.A\Desktop\EXCEL\VERDE PONIENTE-BURITI\MATERIAIS POMPÉU\L101\ALUBAR"  # <-- ALTERE PARA O SEU CAMINHO

# Expressão regular para achar NF
padrao_nf = re.compile(r"NF[:\s]*([0-9]+)", re.IGNORECASE)

nfs_encontradas = []

# Varre todos os PDFs na pasta
for arquivo in os.listdir(PASTA_PDFS):
    if arquivo.lower().endswith(".pdf"):
        caminho_pdf = os.path.join(PASTA_PDFS, arquivo)
        print(f"Lendo {arquivo}...")

        # Abre o PDF
        pdf_doc = fitz.open(caminho_pdf)

        for pagina_idx in range(len(pdf_doc)):
            pagina = pdf_doc[pagina_idx]

            # Renderiza página em imagem (300 dpi aprox.)
            pix = pagina.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # --- Recorte para tentar pegar só o canto direito ---
            largura, altura = img.size
            # Pegando o canto direito (últimos 35% da largura)
            caixa_canto_direito = (int(largura * 0.65), 0, largura, altura)
            img_canto = img.crop(caixa_canto_direito)

            # Extrai texto com OCR
            texto = pytesseract.image_to_string(img_canto, lang="por")

            # Procura todas as NFs na página
            encontrados = padrao_nf.findall(texto)
            if encontrados:
                nfs_encontradas.extend(encontrados)

        pdf_doc.close()

# Conta quantas vezes cada NF apareceu
contador = Counter(nfs_encontradas)

# Caminho do arquivo de saída
arquivo_saida = os.path.join(PASTA_PDFS, "resultado_NFs.txt")

# Escreve os resultados no arquivo
with open(arquivo_saida, "w", encoding="utf-8") as f:
    f.write("--- NFs encontradas ---\n")
    for nf, qtd in contador.items():
        if qtd > 1:
            f.write(f"{nf} (REPETIDA {qtd}x)\n")
        else:
            f.write(f"{nf}\n")

    f.write("\n")
    f.write(f"Total de NFs únicas: {len(contador)}\n")
    f.write(f"Total de NFs encontradas (incluindo repetições): {len(nfs_encontradas)}\n")

print(f"\nProcesso concluído! Resultados salvos em: {arquivo_saida}")
