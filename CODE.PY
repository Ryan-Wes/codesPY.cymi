import os
import re
import pytesseract
import pdfplumber
from PIL import Image
import cv2
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from datetime import datetime

# =========================
# CONFIGURAÇÃO
# =========================
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\wrlopesr\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

CAMINHO_PLANILHA = r"C:\Users\wrlopesr\OneDrive - CYMI CONSTRUÇÕES E PARTICIPAÇÕES S.A\Desktop\NOTAS\EXEMPLOS PRO CÓDIGO PYTHON\PLANILHA DE TESTE.xlsx"

PASTA_NFS = r"C:\Users\wrlopesr\OneDrive - CYMI CONSTRUÇÕES E PARTICIPAÇÕES S.A\Desktop\NOTAS\EXEMPLOS PRO CÓDIGO PYTHON"

# =========================
# FUNÇÕES AUXILIARES
# =========================

def preprocess_image(pil_img):
    """Melhora a imagem para o OCR."""
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return Image.fromarray(thresh)

def ocr_from_pdf(pdf_path):
    """Extrai texto de um PDF usando pdfplumber."""
    texto_total = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pil_image = page.to_image(resolution=300).original
            pil_image = preprocess_image(pil_image)
            texto_total += pytesseract.image_to_string(pil_image, lang="por") + "\n"
    return texto_total

def ocr_from_image(img_path):
    """Extrai texto de uma imagem."""
    pil_img = Image.open(img_path)
    pil_img = preprocess_image(pil_img)
    return pytesseract.image_to_string(pil_img, lang="por")

def extrair_dados(texto):
    """Aplica regex para extrair os campos necessários."""
    texto_limpo = re.sub(r"\s+", " ", texto).strip()

    # Número da NF
    nf = re.search(r"(?:NF-?e|Nota Fiscal)[^\d]{0,10}(\d{5,})", texto_limpo, re.IGNORECASE)

    # Unidade (UN, KG, TON, PC, PÇ, M, CX etc.)
    unid = re.search(r"\b(UN|KG|TON|PC|PÇ|M|CX)\b", texto_limpo, re.IGNORECASE)

    # Quantidade ligada à unidade
    qtd = re.search(r"\b\d{1,6}(?:,\d{1,3})?\s*(?=UN|KG|TON|PC|PÇ|M|CX)\b", texto_limpo, re.IGNORECASE)

    # Volumes / bobinas / conjuntos
    volumes = re.search(r"(?:Volumes?|Bobinas?|Conjuntos?)\D*(\d{1,5})", texto_limpo, re.IGNORECASE)

    # Valor unitário
    valor_unitario = re.search(r"R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}", texto_limpo)

    # Fornecedor
    fornecedor = re.search(r"(ALUBAR|SADEL|SAE TOWERS)", texto_limpo, re.IGNORECASE)

    # Descrição
    descricao = re.search(r"(?<=Descrição\s)[A-Za-z0-9\s\-\/]{10,50}", texto_limpo, re.IGNORECASE)

    return {
        "CODIGO GRAFICO": "",
        "CÓDIGO": "",
        "DATA RECEBIMENTO": datetime.today().strftime("%d/%m/%Y"),
        "DESCRIÇÃO ESPECIFICA": descricao.group(0).strip() if descricao else "",
        "NFE": nf.group(1) if nf else "",
        "UNID": unid.group(0).upper() if unid else "",
        "QTDD": qtd.group(0) if qtd else "",
        "VOLUMES OU BOBINAS OU CONJUNTOS": volumes.group(1) if volumes else "",
        "QTDD POR UNIDADE": "",
        "FORNECEDOR": fornecedor.group(1).upper() if fornecedor else "",
        "VALOR UNITARIO (R$)": valor_unitario.group(0) if valor_unitario else "",
        "VALOR DA NFE (R$)": "",
        "Local": "",
        "Trecho": ""
    }

def encontrar_proxima_linha(sheet):
    """Acha a primeira linha vazia na planilha."""
    for row in range(2, sheet.max_row + 2):
        if all(sheet.cell(row=row, column=col).value is None for col in range(1, sheet.max_column + 1)):
            return row
    return sheet.max_row + 1

# =========================
# PROCESSAMENTO
# =========================

wb = load_workbook(CAMINHO_PLANILHA)
ws = wb.active

amarelo = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

for arquivo in os.listdir(PASTA_NFS):
    caminho_arquivo = os.path.join(PASTA_NFS, arquivo)
    if arquivo.lower().endswith(".pdf"):
        print(f"Processando PDF: {arquivo}")
        texto = ocr_from_pdf(caminho_arquivo)
    elif arquivo.lower().endswith((".png", ".jpg", ".jpeg")):
        print(f"Processando Imagem: {arquivo}")
        texto = ocr_from_image(caminho_arquivo)
    else:
        continue

    # DEBUG: salvar texto extraído para análise
    with open("debug_ocr.txt", "a", encoding="utf-8") as f:
        f.write(f"\n\n=== {arquivo} ===\n")
        f.write(texto)
        f.write("\n=== FIM ===\n")

    dados = extrair_dados(texto)
    linha = encontrar_proxima_linha(ws)

    for col_idx, col_name in enumerate(ws[1], start=1):
        valor = dados.get(col_name.value, "")
        celula = ws.cell(row=linha, column=col_idx, value=valor)
        if valor == "":
            celula.fill = amarelo

wb.save(CAMINHO_PLANILHA)
print("✅ Processamento concluído e planilha atualizada!")
