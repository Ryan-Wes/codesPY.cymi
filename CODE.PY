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

def identificar_fornecedor(texto):
    """Identifica o fornecedor baseado no texto."""
    fornecedores = {
        'ALUBAR': r'alubar|alum[ií]nio|alubar',
        'SADEL': r'sadel',
        'SAE TOWERS': r'sae\s*towers|sae',
        'CYMI': r'cymi',
        'FURUKAWA': r'furukawa',
        'PRYSMIAN': r'prysmian'
    }
    
    texto = texto.lower()
    for fornecedor, padrao in fornecedores.items():
        if re.search(padrao, texto, re.IGNORECASE):
            return fornecedor
    return ""

def extrair_dados(texto):
    """Aplica regex flexível para extrair os campos específicos."""
    texto_limpo = re.sub(r"\s+", " ", texto).strip()
    
    # Padrões de regex para extração
    padrao_nf = r"(?:NF|Nota Fiscal|NFe|Nº\s*)[^\d]{0,10}(\d{3,})"
    padrao_data = r"(\d{2}[-/]\d{2}[-/]\d{4})"
    padrao_valor_unitario = r"(?:valor\s*unit[áa]rio|pre[çc]o\s*unit[áa]rio)[^\d]*([R$]?\s*\d{1,3}(?:\.\d{3})*,\d{2})"
    padrao_valor_total = r"(?:valor\s*total|total\s*da\s*nota)[^\d]*([R$]?\s*\d{1,3}(?:\.\d{3})*,\d{2})"
    padrao_quantidade = r"(?:quantidade|qtd|qtde)[^\d]*(\d+(?:,\d+)?)"
    padrao_unidade = r"(?:unidade|unid\.?)[\s:]*([A-Za-z]{2,3})"
    padrao_descricao = r"(?:descri[çc][ãa]o|especifica[çc][ãa]o)[\s:]*([A-Za-z0-9\sÀ-ÿ\-]+?)(?=\n|$|quantidade|qtd|valor)"
    padrao_volumes = r"(?:volumes|bobinas|conjuntos)[\s:]*(\d+)"
    
    # Extração dos dados
    nf_numero = re.search(padrao_nf, texto_limpo, re.IGNORECASE)
    data_emissao = re.search(padrao_data, texto_limpo)
    valor_unitario = re.search(padrao_valor_unitario, texto_limpo, re.IGNORECASE)
    valor_total = re.search(padrao_valor_total, texto_limpo, re.IGNORECASE)
    quantidade = re.search(padrao_quantidade, texto_limpo, re.IGNORECASE)
    unidade = re.search(padrao_unidade, texto_limpo, re.IGNORECASE)
    descricao = re.search(padrao_descricao, texto_limpo, re.IGNORECASE)
    volumes = re.search(padrao_volumes, texto_limpo, re.IGNORECASE)
    
    fornecedor = identificar_fornecedor(texto_limpo)
    
    return {
        "CODIGO GRAFICO": "",
        "CÓDIGO": "",
        "DATA RECEBIMENTO": datetime.today().strftime("%d/%m/%Y"),
        "DESCRIÇÃO ESPECIFICA": descricao.group(1).strip() if descricao else "",
        "NFE": nf_numero.group(1) if nf_numero else "",
        "UNID": unidade.group(1).upper() if unidade else "",
        "QTDD": quantidade.group(1) if quantidade else "",
        "VOLUMES OU BOBINAS OU CONJUNTOS": volumes.group(1) if volumes else "",
        "QTDD POR UNIDADE": "",
        "FORNECEDOR": fornecedor,
        "VALOR UNITARIO (R$)": valor_unitario.group(1).replace("R$", "").strip() if valor_unitario else "",
        "VALOR DA NFE (R$)": valor_total.group(1).replace("R$", "").strip() if valor_total else "",
        "Local": "",
        "Trecho": ""
    }

def encontrar_proxima_linha(sheet):
    """Acha a primeira linha vazia na planilha."""
    for row in range(2, sheet.max_row + 2):
        if all(sheet.cell(row=row, column=col).value is None for col in range(1, 14)):
            return row
    return sheet.max_row + 1

def mapear_colunas(ws):
    """Mapeia os nomes das colunas para seus índices."""
    mapeamento = {}
    for col in range(1, ws.max_column + 1):
        nome_coluna = ws.cell(row=1, column=col).value
        if nome_coluna:
            mapeamento[nome_coluna.upper()] = col
    return mapeamento

# =========================
# PROCESSAMENTO
# =========================
wb = load_workbook(CAMINHO_PLANILHA)
ws = wb.active
mapeamento_colunas = mapear_colunas(ws)
amarelo = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")

# Ordem das colunas que você quer preencher
colunas_alvo = [
    "DATA RECEBIMENTO",        # Coluna C
    "DESCRIÇÃO ESPECIFICA",    # Coluna D  
    "NFE",                     # Coluna E
    "UNID",                    # Coluna F
    "QTDD",                    # Coluna G
    "VOLUMES OU BOBINAS OU CONJUNTOS",  # Coluna H
    "FORNECEDOR",              # Coluna J
    "VALOR UNITARIO (R$)"      # Coluna K
]

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

    # DEBUG: mostrar texto extraído
    print("\n=== TEXTO EXTRAÍDO DO OCR ===")
    print(texto[:500] + "..." if len(texto) > 500 else texto)
    print("=== FIM DO TEXTO ===\n")

    dados = extrair_dados(texto)
    linha = encontrar_proxima_linha(ws)
    
    print(f"Dados extraídos: {dados}")
    
    # Preencher apenas as colunas específicas
    for coluna_nome in colunas_alvo:
        if coluna_nome in mapeamento_colunas:
            col_idx = mapeamento_colunas[coluna_nome]
            valor = dados.get(coluna_nome, "")
            celula = ws.cell(row=linha, column=col_idx, value=valor)
            
            # Marcar células vazias em amarelo
            if not valor:
                celula.fill = amarelo

    wb.save(CAMINHO_PLANILHA)
    print(f"✅ Dados da NF {dados.get('NFE', 'N/A')} adicionados na linha {linha}")

print("✅ Processamento concluído e planilha atualizada!")